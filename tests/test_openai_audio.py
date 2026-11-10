import json
from pathlib import Path
import sys
import tempfile
import unittest
import wave
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from techchallenge4.openai_audio import transcribe_wav


def sample(path, seconds=1):
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b'\0\0'*int(16000*seconds))
    return path


class AudioBudgetTests(unittest.TestCase):
    def test_success_and_cache_do_not_repeat_request(self):
        with tempfile.TemporaryDirectory() as d:
            calls = []
            path = sample(Path(d)/'a.wav')
            def fake(*args):
                calls.append(args)
                return {'text': 'Transcrição de teste.'}
            first = transcribe_wav(path, Path(d)/'cache', request_fn=fake)
            second = transcribe_wav(path, Path(d)/'cache', request_fn=fake)
            self.assertEqual(len(calls), 1)
            self.assertFalse(first['cache_utilizado'])
            self.assertTrue(second['cache_utilizado'])

    def test_budget_rejection_never_calls_provider(self):
        with tempfile.TemporaryDirectory() as d:
            path = sample(Path(d)/'a.wav')
            def forbidden(*args):
                self.fail('A chamada deveria ter sido bloqueada localmente.')
            for budget in [.021, .000000001]:
                with self.subTest(budget=budget), self.assertRaises(ValueError):
                    transcribe_wav(path, Path(d)/'cache', max_budget_usd=budget, request_fn=forbidden)

    def test_invalid_audio_and_duration_never_call_provider(self):
        with tempfile.TemporaryDirectory() as d:
            for duration in [0, 61]:
                path = sample(Path(d)/f'{duration}.wav', duration)
                with self.subTest(duration=duration), self.assertRaises(ValueError):
                    transcribe_wav(path, Path(d)/'cache', request_fn=lambda *args: self.fail('Não enviar.'))

    def test_timeout_and_empty_response_keep_reservation(self):
        with tempfile.TemporaryDirectory() as d:
            path = sample(Path(d)/'a.wav')
            def timeout(*args):
                raise TimeoutError('mock')
            with self.assertRaises(TimeoutError):
                transcribe_wav(path, Path(d)/'cache', request_fn=timeout)
            with self.assertRaises(ValueError):
                transcribe_wav(path, Path(d)/'cache', request_fn=lambda *args: {'text': ' '})
            ledger = json.loads((Path(d)/'cache/orcamento_transcricao.json').read_text(encoding='utf8'))
            self.assertEqual(len(ledger['chamadas']), 2)
            self.assertTrue(all(c['estado']=='falha_reserva_mantida' for c in ledger['chamadas']))
            self.assertTrue(all(c['custo_contabilizado_usd'] > 0 for c in ledger['chamadas']))

    def test_six_failures_block_seventh_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            path = sample(Path(d)/'a.wav')
            calls = []
            def fail(*args):
                calls.append(1)
                raise TimeoutError('mock')
            for _ in range(6):
                with self.assertRaises(TimeoutError):
                    transcribe_wav(path, Path(d)/'cache', request_fn=fail)
            with self.assertRaises(ValueError):
                transcribe_wav(path, Path(d)/'cache', request_fn=fail)
            self.assertEqual(len(calls), 6)

    def test_corrupt_cache_is_rejected_without_spending(self):
        with tempfile.TemporaryDirectory() as d:
            path = sample(Path(d)/'a.wav')
            cache = Path(d)/'cache'
            transcribe_wav(path, cache, request_fn=lambda *args: {'text': 'Teste.'})
            target = next(p for p in cache.glob('*.json') if p.name != 'orcamento_transcricao.json')
            saved = json.loads(target.read_text(encoding='utf8'))
            saved['sha256_audio'] = 'hash_incorreto'
            target.write_text(json.dumps(saved), encoding='utf8')
            with self.assertRaises(ValueError):
                transcribe_wav(path, cache, request_fn=lambda *args: self.fail('Não enviar.'))


if __name__ == '__main__':
    unittest.main()
