import { MousePointerClick } from 'lucide-react'

interface Props {
  size?: number
  color?: string
}

export default function AgentLogo({ size = 40, color = '#111111' }: Props) {
  const iconSize = Math.round(size * 0.52)
  const radius = Math.round(size * 0.25)
  return (
    <div
      style={{ width: size, height: size, borderRadius: radius }}
      className="flex items-center justify-center flex-shrink-0"
    >
      <MousePointerClick size={iconSize} color={color} strokeWidth={2.2} style={{ transform: 'scaleX(-1)' }} />
    </div>
  )
}
