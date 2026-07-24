import { AlertTriangle } from 'lucide-react'

interface Props {
  warnings: string[]
}

export default function ConcentrationWarnings({ warnings }: Props) {
  if (!warnings.length) return null

  return (
    <div className="space-y-2">
      {warnings.map((w, i) => (
        <div
          key={i}
          className="flex items-start gap-3 px-4 py-3 bg-amber-50 border border-amber-100 rounded-xl"
        >
          <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" strokeWidth={2} />
          <p className="text-xs text-amber-800 leading-relaxed">{w}</p>
        </div>
      ))}
    </div>
  )
}
