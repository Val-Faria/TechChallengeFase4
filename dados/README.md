# Origem e preparação das mídias

As seis gravações em audio/ foram produzidas por síntese local Windows SAPI, com as vozes Microsoft Daniel e Microsoft Maria. O manifesto registra as frases, vozes e hashes. Elas foram reservadas para inspeção funcional após o treinamento do classificador.

As montagens em video/ derivam dos quadros do dataset **Uterus v4**, disponibilizado por **Machinelearning**, com licença declarada **CC BY 4.0** na exportação Roboflow. Fonte: https://universe.roboflow.com/machinelearning-yekk6/uterus-qn1he/dataset/4. Licença: https://creativecommons.org/licenses/by/4.0/.

O arquivo de exportação original está em video/datasets/Uterus.v4i.yolov8.zip, a partir da raiz do repositório. Cada imagem foi repetida por dois segundos nas montagens. A montagem test usa 37 quadros do teste. A montagem blind_holdout usa 60 imagens da origem reservada. Os tempos representam essa construção. A transformação e os prefixos de origem estão registrados em evidence/video_dataset_auditoria.json e evidence/video_inferencia_nova.json.

As cópias em video/visualizacao/ foram recodificadas em WebM/VP8 para reprodução nos navegadores. A inferência utiliza os arquivos MP4 originais. As imagens exibidas durante o processamento vêm diretamente do detector na execução atual.

As referências em referencias/ foram calculadas com gravações anteriores das mesmas vozes. Elas permitem comparar pausas e trechos vocais sem incluir o WAV avaliado na referência.
