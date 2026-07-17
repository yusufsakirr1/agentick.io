import { useEffect, useState } from 'react'

const STAGES = [
  { text: 'Soru analiz ediliyor', duration: 4000 },
  { text: 'SQL ve belgeler taranıyor', duration: 6000 },
  { text: 'Sonuçlar değerlendiriliyor', duration: 4000 },
  { text: 'Yanıt hazırlanıyor', duration: 99999 },
]

export default function ThinkingIndicator() {
  const [stageIndex, setStageIndex] = useState(0)
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    setStageIndex(0)
    setVisible(true)
  }, [])

  useEffect(() => {
    if (stageIndex >= STAGES.length - 1) return

    const stage = STAGES[stageIndex]

    // Önce fade-out, sonra stage değişimi, sonra fade-in
    const timer = setTimeout(() => {
      setVisible(false)
      setTimeout(() => {
        setStageIndex(i => Math.min(i + 1, STAGES.length - 1))
        setVisible(true)
      }, 400)
    }, stage.duration)

    return () => clearTimeout(timer)
  }, [stageIndex])

  return (
    <div className="flex items-center gap-3">
      {/* Pulsing dot */}
      <div className="flex gap-1 items-center flex-shrink-0">
        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
      </div>

      {/* Stage text */}
      <span
        className="text-sm text-gray-500 transition-opacity duration-300"
        style={{ opacity: visible ? 1 : 0 }}
      >
        {STAGES[stageIndex].text}
        <span className="inline-flex gap-0.5 ml-0.5">
          <span className="animate-[blink_1.4s_ease-in-out_infinite]">.</span>
          <span className="animate-[blink_1.4s_ease-in-out_0.2s_infinite]">.</span>
          <span className="animate-[blink_1.4s_ease-in-out_0.4s_infinite]">.</span>
        </span>
      </span>

      <style>{`
        @keyframes blink {
          0%, 80%, 100% { opacity: 0.2 }
          40% { opacity: 1 }
        }
      `}</style>
    </div>
  )
}
