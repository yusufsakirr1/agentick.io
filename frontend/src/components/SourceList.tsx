import { useState } from 'react'
import { FileText, Table2, Newspaper, ChevronDown, ExternalLink } from 'lucide-react'
import type { AgentSource } from '../api/client'

interface Props {
  sources: AgentSource[]
}

/** Bir PDF sayfası (veya sayfasız belge girdisi) ile ait olduğu kaynak kaydı */
interface PageEntry {
  page: number | null
  source: AgentSource
}

interface FileGroup {
  file: string
  entries: PageEntry[]
}

/**
 * PDF kaynaklarını dosya bazında gruplar, her dosyanın sayfalarını sıraya dizer.
 * Aynı sayfa birden fazla chunk'tan gelirse en yüksek skorlu olan tutulur.
 */
function groupPdfSources(sources: AgentSource[]): FileGroup[] {
  const groups = new Map<string, Map<string, PageEntry>>()

  for (const source of sources) {
    if (source.type !== 'vector' && source.type !== 'pdf') continue
    const file = source.source_file || 'Yüklenen belge'
    if (!groups.has(file)) groups.set(file, new Map())
    const pages = source.pages?.length ? source.pages : [null]

    for (const page of pages) {
      const key = page === null ? 'belge' : String(page)
      const existing = groups.get(file)!.get(key)
      if (!existing || source.score > existing.source.score) {
        groups.get(file)!.set(key, { page, source })
      }
    }
  }

  return Array.from(groups.entries()).map(([file, entryMap]) => ({
    file,
    entries: Array.from(entryMap.values()).sort(
      (a, b) => (a.page ?? Infinity) - (b.page ?? Infinity),
    ),
  }))
}

function formatDate(value?: string | null): string {
  if (!value) return ''
  return value.slice(0, 10)
}

export default function SourceList({ sources }: Props) {
  const [open, setOpen] = useState(false)
  const [openKey, setOpenKey] = useState<string | null>(null)

  if (!sources?.length) return null

  const pdfGroups = groupPdfSources(sources)
  const sqlSources = sources.filter(s => s.type === 'sql')
  const newsSources = sources.filter(s => s.type === 'news')

  const pageCount = pdfGroups.reduce((n, g) => n + g.entries.length, 0)

  const toggleSnippet = (key: string) => setOpenKey(prev => (prev === key ? null : key))

  return (
    <div className="w-full mt-1">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-[11px] font-medium text-gray-400
                   hover:text-gray-600 transition-colors cursor-pointer"
      >
        <FileText className="w-3.5 h-3.5" strokeWidth={1.8} />
        Kaynaklar ({sources.length})
        {pageCount > 0 && (
          <span className="text-gray-300">· {pageCount} sayfa</span>
        )}
        <ChevronDown
          className={`w-3.5 h-3.5 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="mt-2 space-y-3 rounded-xl border border-gray-100 bg-gray-50/60 px-4 py-3">

          {/* PDF / KAP raporu kaynakları */}
          {pdfGroups.map(group => (
            <div key={group.file}>
              <div className="flex items-center gap-1.5 mb-1.5">
                <FileText className="w-3.5 h-3.5 text-purple-500 flex-shrink-0" strokeWidth={1.8} />
                <span className="text-[11px] font-semibold text-gray-700 truncate" title={group.file}>
                  {group.file}
                </span>
              </div>

              <div className="flex flex-wrap gap-1.5 pl-5">
                {group.entries.map(entry => {
                  const key = `${group.file}-${entry.page ?? 'belge'}`
                  const isOpen = openKey === key
                  return (
                    <button
                      key={key}
                      onClick={() => toggleSnippet(key)}
                      title={entry.source.section || undefined}
                      className={`text-[11px] font-mono px-2 py-0.5 rounded-md border transition-colors cursor-pointer
                        ${isOpen
                          ? 'bg-purple-600 text-white border-purple-600'
                          : 'bg-white text-purple-700 border-purple-200 hover:border-purple-400'
                        }`}
                    >
                      {entry.page === null ? 'belge' : `s.${entry.page}`}
                    </button>
                  )
                })}
              </div>

              {group.entries.map(entry => {
                const key = `${group.file}-${entry.page ?? 'belge'}`
                if (openKey !== key) return null
                return (
                  <div key={`${key}-snippet`} className="mt-2 ml-5 rounded-lg bg-white border border-gray-100 px-3 py-2">
                    <p className="text-[10px] font-medium text-gray-400 mb-1">
                      {entry.page !== null && `Sayfa ${entry.page}`}
                      {entry.source.section && ` · ${entry.source.section}`}
                      {entry.source.score > 0 && ` · %${Math.round(entry.source.score * 100)} eşleşme`}
                    </p>
                    <p className="text-[11px] text-gray-600 leading-relaxed">
                      {entry.source.snippet}
                    </p>
                  </div>
                )
              })}
            </div>
          ))}

          {/* Finansal veri (yfinance / SQLite) */}
          {sqlSources.map((source, i) => (
            <div key={`sql-${i}`} className="flex items-start gap-1.5">
              <Table2 className="w-3.5 h-3.5 text-blue-500 flex-shrink-0 mt-0.5" strokeWidth={1.8} />
              <div className="min-w-0">
                <p className="text-[11px] font-semibold text-gray-700">
                  Finansal veri · {source.tables?.length ? source.tables.join(', ') : 'yfinance'}
                </p>
                {source.period_range && (
                  <p className="text-[10px] text-gray-400">{source.period_range}</p>
                )}
              </div>
            </div>
          ))}

          {/* Haberler */}
          {newsSources.map((source, i) => (
            <div key={`news-${i}`} className="flex items-start gap-1.5">
              <Newspaper className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" strokeWidth={1.8} />
              <div className="min-w-0 flex-1">
                {source.link ? (
                  <a
                    href={source.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] font-semibold text-gray-700 hover:text-amber-600
                               transition-colors inline-flex items-center gap-1"
                  >
                    <span className="truncate">{source.title || source.citation}</span>
                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                  </a>
                ) : (
                  <p className="text-[11px] font-semibold text-gray-700 truncate">
                    {source.title || source.citation}
                  </p>
                )}
                {source.published_at && (
                  <p className="text-[10px] text-gray-400">{formatDate(source.published_at)}</p>
                )}
              </div>
            </div>
          ))}

          <p className="text-[10px] text-gray-300 pt-1 border-t border-gray-100">
            Bu kaynaklar yanıtı üretirken modele verilen alıntılardır.
          </p>
        </div>
      )}
    </div>
  )
}
