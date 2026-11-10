$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskDestination = Join-Path $taskRoot 'dados_privados\midias_complementares'
New-Item -ItemType Directory -Force -Path $taskDestination | Out-Null
$taskCases = @(
    @{ id='daniel-ref1'; voice='Microsoft Daniel'; role='referencia'; text='Durante a visita de hoje relatei como foi minha caminhada pelo jardim da unidade.' },
    @{ id='daniel-ref2'; voice='Microsoft Daniel'; role='referencia'; text='Anotei o horario das atividades e conversei sobre minha rotina de descanso com a profissional.' },
    @{ id='daniel-prova'; voice='Microsoft Daniel'; role='verificacao_reservada'; text='Gostaria de explicar com calma como me senti durante os exercicios realizados nesta manha.' },
    @{ id='maria-ref1'; voice='Microsoft Maria Desktop'; role='referencia'; text='Na ultima conversa descrevi minhas atividades diarias e os momentos reservados para o repouso.' },
    @{ id='maria-ref2'; voice='Microsoft Maria Desktop'; role='referencia'; text='Acompanhei as orientacoes da equipe e registrei no caderno as observacoes sobre minha rotina.' },
    @{ id='maria-prova'; voice='Microsoft Maria Desktop'; role='verificacao_reservada'; text='Nesta consulta quero conversar sobre os exercicios que pratiquei e como organizei meu descanso.' }
)
$taskSynth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$taskManifest = @()
try {
    foreach ($taskCase in $taskCases) {
        $taskPath = Join-Path $taskDestination ($taskCase.id + '.wav')
        if (Test-Path -LiteralPath $taskPath) { throw "Arquivo ja existe; nao sobrescrever midia reservada: $($taskCase.id)" }
        $taskSynth.SelectVoice($taskCase.voice)
        $taskSynth.Rate = 0
        $taskSynth.SetOutputToWaveFile($taskPath)
        $taskSynth.Speak($taskCase.text)
        $taskSynth.SetOutputToNull()
        $taskManifest += @{ id=$taskCase.id; voz=$taskCase.voice; papel=$taskCase.role; texto=$taskCase.text; arquivo=($taskCase.id+'.wav'); sha256=(Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLower() }
    }
} finally { $taskSynth.Dispose() }
@{ origem='Windows SAPI; sintese local; sem paciente real'; simulado=$true; casos=$taskManifest } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskDestination 'manifesto_sintese.json') -Encoding UTF8
Write-Output 'Seis novas gravacoes sinteticas salvas; referencias e provas separadas.'
