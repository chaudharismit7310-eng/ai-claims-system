import { useState, useRef } from 'react'

function VoiceInput({ onTranscript }) {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [supported, setSupported] = useState(
    'webkitSpeechRecognition' in window || 'SpeechRecognition' in window
  )
  const recognitionRef = useRef(null)

  const startRecording = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    
    if (!SpeechRecognition) {
      alert('Voice input not supported in this browser. Please use Chrome.')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-IN'

    recognition.onstart = () => setIsRecording(true)

    recognition.onresult = (event) => {
      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript
        } else {
          interimTranscript += event.results[i][0].transcript
        }
      }

      const fullText = finalTranscript || interimTranscript
      setTranscript(fullText)
      if (finalTranscript) onTranscript(finalTranscript)
    }

    recognition.onerror = (event) => {
      console.error('Speech error:', event.error)
      setIsRecording(false)
    }

    recognition.onend = () => setIsRecording(false)

    recognitionRef.current = recognition
    recognition.start()
  }

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      setIsRecording(false)
    }
  }

  if (!supported) return null

  return (
    <div className="flex items-center gap-2 mt-2">
      <button
        type="button"
        onClick={isRecording ? stopRecording : startRecording}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
          isRecording
            ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
            : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
        }`}
      >
        {isRecording ? (
          <>
            <span className="w-2 h-2 bg-white rounded-full"></span>
            Stop Recording
          </>
        ) : (
          <>
            🎤 Voice Input
          </>
        )}
      </button>
      {transcript && (
        <span className="text-xs text-gray-500 truncate max-w-xs">
          "{transcript}"
        </span>
      )}
    </div>
  )
}

export default VoiceInput