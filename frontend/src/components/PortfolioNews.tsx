import { useState, useEffect } from 'react'
import { Newspaper, ExternalLink } from 'lucide-react'
import { fetchPortfolioNews, type NewsArticle } from '../api/client'

interface Props {
  tickers: string[]
}

export default function PortfolioNews({ tickers }: Props) {
  const [articles, setArticles] = useState<NewsArticle[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!tickers.length) return
    let cancelled = false
    setLoading(true)

    fetchPortfolioNews(tickers)
      .then(res => {
        if (!cancelled) setArticles(res.articles ?? [])
      })
      .catch(() => {
        if (!cancelled) setArticles([])
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [tickers.join(',')])

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5">
      <div className="flex items-center gap-2 mb-4">
        <Newspaper className="w-4 h-4 text-gray-400" strokeWidth={1.8} />
        <h3 className="text-sm font-semibold text-gray-900">Portföy Haberleri</h3>
      </div>

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-gray-50 rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {!loading && articles.length === 0 && (
        <p className="text-xs text-gray-400 text-center py-4">Haber bulunamadı</p>
      )}

      {!loading && articles.length > 0 && (
        <div className="space-y-3">
          {articles.map((a, i) => (
            <div key={i} className="px-4 py-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
              <div className="flex items-start gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {a.source && (
                      <span className="text-[10px] font-medium text-gray-500 bg-white px-2 py-0.5 rounded-full border border-gray-200">
                        {a.source}
                      </span>
                    )}
                    <span className="text-[10px] font-mono text-gray-900 bg-gray-200 px-1.5 py-0.5 rounded font-bold">
                      {a.ticker}
                    </span>
                    {a.published_at && (
                      <span className="text-[10px] text-gray-400">{a.published_at.slice(0, 10)}</span>
                    )}
                  </div>
                  <p className="text-xs font-medium text-gray-900 leading-relaxed line-clamp-2">
                    {a.title}
                  </p>
                  {a.summary && (
                    <p className="text-[11px] text-gray-500 mt-1 line-clamp-2 leading-relaxed">
                      {a.summary}
                    </p>
                  )}
                </div>
                {a.link && (
                  <a
                    href={a.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 text-gray-300 hover:text-gray-500 transition-colors flex-shrink-0"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
