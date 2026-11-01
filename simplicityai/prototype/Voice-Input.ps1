param([ValidateSet('Probe','Listen')][string]$Mode='Probe')
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
$engine=$null
try {
    Add-Type -AssemblyName System.Speech
    $installed=@([System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers())
    if(-not $installed.Count){throw 'No installed Windows speech-recognition engine. Typing is still available.'}
    $preferred=@($installed|Where-Object {$_.Culture.Name -eq 'en-US'})
    $info=if($preferred.Count){$preferred[0]}else{$installed[0]}
    if($Mode -eq 'Probe'){
        @{state='ready';language=$info.Culture.Name;message='Windows recognition engine found. Microphone access is tested only when you click Speak.'}|ConvertTo-Json -Compress
    }else{
        $engine=[System.Speech.Recognition.SpeechRecognitionEngine]::new($info)
        $engine.LoadGrammar([System.Speech.Recognition.DictationGrammar]::new())
        $engine.SetInputToDefaultAudioDevice()
        $engine.BabbleTimeout=[TimeSpan]::FromSeconds(15)
        @{state='listening';message='Listening. Say one short sentence, then pause.'}|ConvertTo-Json -Compress
        [Console]::Out.Flush()
        $result=$engine.Recognize([TimeSpan]::FromSeconds(12))
        if($null -eq $result){
            @{state='no_speech';message='No clear speech was recognized. Try again or type your issue.'}|ConvertTo-Json -Compress
        }else{
            @{state='transcribed';text=$result.Text;confidence=$result.Confidence;message='Review and edit the words before using them.'}|ConvertTo-Json -Compress
        }
    }
}catch{
    @{state='unavailable';message='Windows voice input is unavailable. Check the default microphone, VMware audio access, Windows microphone permission and installed speech language. Typing still works.'}|ConvertTo-Json -Compress
}finally{if($null -ne $engine){$engine.Dispose()}}
