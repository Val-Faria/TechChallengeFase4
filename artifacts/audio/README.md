# Modelo emocional congelado

`modelo_audio_1180.joblib` é o Random Forest ajustado somente no treino, com SHA-256 `505c882da687e90e2bca57b3d92436338b57a5ec450a96eecefec989b0e2dd05`. O arquivo foi gerado nesta consolidação e é versionado para permitir inferência sem novo treinamento.

Instalar `requirements-audio.txt`, incluindo scikit-learn 1.6.1, antes de carregá-lo. Usar `scripts/audio_infer.py`, que confere o hash contra `manifesto_audio.json`. Não carregar artefatos Joblib de origem desconhecida.

O modelo classifica as três categorias emocionais sintéticas do corpus; não diagnostica condições médicas. Sua reserva de dados e suas limitações constam em `evidence/audio_reproducao.json`. Arquivos de características/cache necessários para repetir a extração ficam no backup privado e podem ser regenerados a partir do ZIP via Git LFS.
