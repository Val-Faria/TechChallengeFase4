"""Caixa local persistente com confirmação de registro e replay mensurado.

Replay reproduz resultados pré-calculados, não mede latência de inferência.
"""
from __future__ import annotations
from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import time


def now():
    return datetime.now(timezone.utc).isoformat()


class AlertStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS alerts (
              result_id TEXT PRIMARY KEY, case_id TEXT NOT NULL,
              received_utc TEXT NOT NULL, payload TEXT NOT NULL,
              acknowledged_utc TEXT, reviewer TEXT);
            CREATE TABLE IF NOT EXISTS audit (
              sequence INTEGER PRIMARY KEY AUTOINCREMENT,
              at_utc TEXT NOT NULL, action TEXT NOT NULL,
              result_id TEXT NOT NULL, detail TEXT NOT NULL);
            """)

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def deliver(self, result):
        if not result.get("requer_revisao"):
            return {"destino": "caixa_local_equipe_medica", "status": "sem_revisao_solicitada"}
        payload = deepcopy(result)
        received = now()
        receipt = {"destino": "caixa_local_equipe_medica", "status": "persistido",
                   "recebido_em_utc": received,
                   "confirmacao": "gravacao_transacional_sqlite",
                   "entrega_hospitalar": False}
        payload["entrega"] = receipt
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False)
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT payload FROM alerts WHERE result_id=?",
                                  (result["id_resultado"],)).fetchone()
            if existing:
                saved = json.loads(existing["payload"])
                def identity(value):
                    return {k: v for k, v in value.items()
                            if k not in {"entrega", "gerado_em_utc"}}
                if identity(saved) != identity(payload):
                    raise ValueError("Identificador repetido com conteúdo divergente.")
                return saved["entrega"]
            db.execute("INSERT INTO alerts VALUES (?,?,?,?,NULL,NULL)",
                       (result["id_resultado"], result["id_caso"], received, text))
            db.execute("INSERT INTO audit(at_utc,action,result_id,detail) VALUES (?,?,?,?)",
                       (received, "entrega_local", result["id_resultado"],
                        json.dumps({"sha256_payload": hashlib.sha256(text.encode()).hexdigest()})))
        return receipt

    def acknowledge(self, result_id, reviewer="revisor_local"):
        if not isinstance(reviewer, str) or not 1 <= len(reviewer.strip()) <= 80:
            raise ValueError("Informe um nome de revisor com até 80 caracteres.")
        with self._connection() as db:
            row = db.execute("SELECT acknowledged_utc FROM alerts WHERE result_id=?",
                             (result_id,)).fetchone()
            if row is None:
                raise KeyError("Resultado não encontrado.")
            if row["acknowledged_utc"]:
                return False
            when = now()
            db.execute("UPDATE alerts SET acknowledged_utc=?,reviewer=? WHERE result_id=?",
                       (when, reviewer.strip(), result_id))
            db.execute("INSERT INTO audit(at_utc,action,result_id,detail) VALUES (?,?,?,?)",
                       (when, "revisao_confirmada", result_id,
                        json.dumps({"revisor": reviewer.strip()}, ensure_ascii=False)))
        return True

    def list_alerts(self):
        with self._connection() as db:
            rows = db.execute("SELECT * FROM alerts ORDER BY received_utc,result_id").fetchall()
        return [{"resultado": json.loads(r["payload"]),
                 "recebido_em_utc": r["received_utc"],
                 "revisado_em_utc": r["acknowledged_utc"], "revisor": r["reviewer"]}
                for r in rows]

    def audit_log(self):
        with self._connection() as db:
            return [dict(row) for row in db.execute("SELECT * FROM audit ORDER BY sequence")]


def replay_events(events, store, *, speed=0.0):
    """Replay por ordem temporal. speed=0 evita espera; 1 reproduz o tempo original.

    Cada evento tem offset_s e resultado. Duração medida cobre somente entrega local.
    """
    from .core import numero_finito
    speed = numero_finito(speed, "velocidade_replay", 0)
    previous = 0.0
    rows = []
    for event in events:
        offset = numero_finito(event["offset_s"], "offset_s", 0)
        if offset < previous:
            raise ValueError("Replay exige offsets em ordem crescente.")
        if speed:
            time.sleep((offset - previous) / speed)
        previous = offset
        started = time.perf_counter()
        receipt = store.deliver(event["resultado"])
        rows.append({"offset_origem_s": offset,
                     "id_resultado": event["resultado"]["id_resultado"],
                     "latencia_entrega_local_ms": (time.perf_counter()-started)*1000,
                     "escopo_latencia": "persistencia_local_sem_inferencia",
                     "modo": "replay_acelerado" if not speed else "replay_temporizado",
                     "entrega": receipt})
    return rows
