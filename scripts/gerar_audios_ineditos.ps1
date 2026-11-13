param([string]$Destino = "$PSScriptRoot/../dados_privados/audio_inedito")
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$taskOut = [System.IO.Path]::GetFullPath($Destino)
New-Item -ItemType Directory -Force -Path $taskOut | Out-Null
$taskCases = @(
    @{id='novo-01'; texto='Hoje consegui caminhar pelo corredor e conversei tranquilamente com a equipe. Não estou com dor nem com falta de ar.'; voz='Microsoft Daniel'; taxa=0; esperado='negacao'},
    @{id='novo-02'; texto='Estou preocupada com o exame de amanhã. Meu coração parece acelerado e gostaria de conversar com alguém da equipe.'; voz='Microsoft Maria Desktop'; taxa=1; esperado='preocupacao'},
    @{id='novo-03'; texto='Desde o começo da tarde sinto falta de ar e uma tontura que não passa. Preciso que a equipe venha me avaliar.'; voz='Microsoft Daniel'; taxa=-1; esperado='mencao_critica'},
    @{id='novo-04'; texto='Sinto saudade da minha família e tenho ficado desanimada durante a internação. Gostaria de receber apoio.'; voz='Microsoft Maria Desktop'; taxa=-2; esperado='desanimo'},
    @{id='novo-05'; texto='A profissional perguntou sobre sangramento, mas respondi que não tive sangramento. A consulta terminou normalmente.'; voz='Microsoft Daniel'; taxa=0; esperado='negacao'},
    @{id='novo-06'; texto='Estou conseguindo descansar melhor. A dor diminuiu depois do atendimento e quero continuar seguindo as orientações recebidas.'; voz='Microsoft Maria Desktop'; taxa=0; esperado='melhora'}
)
$taskSynth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    foreach ($taskCase in $taskCases) {
        $taskSynth.SelectVoice($taskCase.voz)
        $taskSynth.Rate = $taskCase.taxa
        $taskPath = Join-Path $taskOut ($taskCase.id + '.wav')
        $taskSynth.SetOutputToWaveFile($taskPath)
        $taskSynth.Speak($taskCase.texto)
        $taskSynth.SetOutputToNull()
        $taskCase.arquivo = $taskCase.id + '.wav'
        $taskCase.sha256 = (Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLower()
    }
} finally { $taskSynth.Dispose() }
@{origem='Sintese local Windows SAPI'; sintetico=$true; uso='Verificacao externa de software; sem rotulos clinicos ou emocionais validados'; treino=$false; validacao=$false; teste_desenvolvimento=$false; casos=$taskCases} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskOut 'manifesto.json') -Encoding utf8
Write-Output 'Seis audios novos e manifesto salvos; nenhuma chamada paga.'
