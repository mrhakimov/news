import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'

interface MarkdownRendererProps {
  content: string
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="prose prose-sm max-w-none text-gray-100 prose-headings:text-white prose-strong:text-white prose-em:text-gray-200 prose-code:text-gray-200 prose-code:bg-stone-700 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-stone-800 prose-pre:border prose-pre:border-stone-600">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
      components={{
        // Customize heading styles
        h1: ({ children }) => <h1 className="text-xl font-bold text-white mb-3 mt-4">{children}</h1>,
        h2: ({ children }) => <h2 className="text-lg font-semibold text-white mb-2 mt-3">{children}</h2>,
        h3: ({ children }) => <h3 className="text-md font-semibold text-white mb-2 mt-2">{children}</h3>,
        
        // Customize list styles
        ul: ({ children }) => <ul className="list-disc list-inside text-gray-100 space-y-1 my-2">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-inside text-gray-100 space-y-1 my-2">{children}</ol>,
        li: ({ children }) => <li className="text-gray-100">{children}</li>,
        
        // Customize paragraph styles
        p: ({ children }) => <p className="text-gray-100 mb-2 leading-relaxed">{children}</p>,
        
        // Customize strong and emphasis
        strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
        em: ({ children }) => <em className="italic text-gray-200">{children}</em>,
        
        // Customize code blocks
        code: ({ children, className }) => {
          const isInline = !className
          if (isInline) {
            return <code className="bg-stone-700 text-gray-200 px-1 py-0.5 rounded text-sm font-mono">{children}</code>
          }
          return (
            <code className={`${className} text-gray-200`}>
              {children}
            </code>
          )
        },
        
        // Customize pre blocks
        pre: ({ children }) => (
          <pre className="bg-stone-800 border border-stone-600 rounded-md p-3 overflow-x-auto my-3">
            {children}
          </pre>
        ),
        
        // Customize blockquotes
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-stone-600 pl-4 italic text-gray-300 my-3">
            {children}
          </blockquote>
        ),
        
        // Customize tables
        table: ({ children }) => (
          <div className="overflow-x-auto my-3">
            <table className="min-w-full border border-stone-600 rounded-md">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-stone-800">{children}</thead>,
        tbody: ({ children }) => <tbody className="bg-stone-900">{children}</tbody>,
        tr: ({ children }) => <tr className="border-b border-stone-600">{children}</tr>,
        th: ({ children }) => <th className="px-3 py-2 text-left text-white font-semibold">{children}</th>,
        td: ({ children }) => <td className="px-3 py-2 text-gray-100">{children}</td>,
      }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
} 
