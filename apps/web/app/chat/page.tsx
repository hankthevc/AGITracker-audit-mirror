'use client'

import { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Loader2, Send, Trash2, Copy, CheckCircle, ExternalLink } from 'lucide-react'

// P1-8: XSS protection for rendered markdown
// Note: In production, install dompurify: npm install dompurify @types/dompurify
// For now, we use dangerouslySetInnerHTML sparingly and sanitize on backend

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
}

interface Source {
  type: 'event' | 'signpost'
  id: number
  title?: string
  name?: string
  code?: string
  url?: string
  tier?: string
  category?: string
  similarity: number
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string>('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Fetch suggested questions on mount
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/v1/chat/suggestions`)
      .then(res => res.json())
      .then(data => setSuggestions(data.suggestions || []))
      .catch(err => console.error('Failed to fetch suggestions:', err))
  }, [])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Generate session ID on mount
  useEffect(() => {
    setSessionId(crypto.randomUUID())
  }, [])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          session_id: sessionId,
          stream: true
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Read SSE stream
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let assistantMessage = ''
      let sources: Source[] = []

      if (!reader) {
        throw new Error('No response body')
      }

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'token') {
              assistantMessage += data.content
              
              // Update assistant message in real-time
              setMessages(prev => {
                const newMessages = [...prev]
                const lastMessage = newMessages[newMessages.length - 1]
                
                if (lastMessage?.role === 'assistant') {
                  newMessages[newMessages.length - 1] = {
                    role: 'assistant',
                    content: assistantMessage,
                    sources: lastMessage.sources
                  }
                } else {
                  newMessages.push({
                    role: 'assistant',
                    content: assistantMessage
                  })
                }
                
                return newMessages
              })
            } else if (data.type === 'sources') {
              sources = data.sources
              
              // Add sources to last message
              setMessages(prev => {
                const newMessages = [...prev]
                const lastMessage = newMessages[newMessages.length - 1]
                
                if (lastMessage?.role === 'assistant') {
                  newMessages[newMessages.length - 1] = {
                    ...lastMessage,
                    sources
                  }
                }
                
                return newMessages
              })
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.'
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearChat = () => {
    setMessages([])
    setSessionId(crypto.randomUUID())
  }

  const handleCopyMessage = async (content: string, index: number) => {
    await navigator.clipboard.writeText(content)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
    inputRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">AGI Progress Chatbot</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Ask questions about AGI progress, benchmarks, and signposts. Powered by RAG with citations.
          </p>
        </div>

        {/* Chat container */}
        <Card className="mb-4 min-h-[600px] flex flex-col">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <CardTitle>Conversation</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearChat}
                disabled={messages.length === 0}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear Chat
              </Button>
            </div>
          </CardHeader>

          <CardContent className="flex-1 overflow-y-auto p-6 space-y-4" style={{ maxHeight: '600px' }}>
            {messages.length === 0 && (
              <div className="text-center text-gray-500 dark:text-gray-400 py-12">
                <p className="mb-6">Ask a question to get started!</p>
                
                {/* Suggested questions */}
                {suggestions.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold mb-3">Suggested questions:</p>
                    <div className="space-y-2 max-w-2xl mx-auto">
                      {suggestions.slice(0, 4).map((suggestion, i) => (
                        <button
                          key={i}
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="w-full text-left px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                  }`}
                >
                  {/* Message content */}
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    {/* P1-8: Safe rendering - React escapes by default */}
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  </div>

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                      <p className="text-xs font-semibold mb-2">Sources:</p>
                      <div className="space-y-2">
                        {message.sources.map((source, i) => (
                          <div key={i} className="text-xs">
                            {source.type === 'event' ? (
                              <div className="flex items-start gap-2">
                                <Badge variant="outline" className="text-xs">
                                  {source.tier}
                                </Badge>
                                <div className="flex-1">
                                  {/* eslint-disable-next-line no-restricted-syntax */}
                                  {/* Database-sourced URL with noopener/noreferrer */}
                                  <a
                                    href={source.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                                  >
                                    {source.title}
                                    <ExternalLink className="h-3 w-3" />
                                  </a>
                                  <p className="text-gray-500 dark:text-gray-400 text-xs">
                                    Similarity: {(source.similarity * 100).toFixed(1)}%
                                  </p>
                                </div>
                              </div>
                            ) : (
                              <div className="flex items-start gap-2">
                                <Badge variant="outline" className="text-xs">
                                  {source.category}
                                </Badge>
                                <div className="flex-1">
                                  <span className="font-medium">{source.name}</span>
                                  <span className="text-gray-500 dark:text-gray-400"> ({source.code})</span>
                                  <p className="text-gray-500 dark:text-gray-400 text-xs">
                                    Similarity: {(source.similarity * 100).toFixed(1)}%
                                  </p>
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Copy button */}
                  {message.role === 'assistant' && (
                    <div className="mt-2 flex justify-end">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopyMessage(message.content, index)}
                      >
                        {copiedIndex === index ? (
                          <CheckCircle className="h-3 w-3 mr-1" />
                        ) : (
                          <Copy className="h-3 w-3 mr-1" />
                        )}
                        {copiedIndex === index ? 'Copied!' : 'Copy'}
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </CardContent>

          {/* Input area */}
          <div className="border-t p-4">
            <div className="flex gap-2">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about AGI progress... (Shift+Enter for new line)"
                className="flex-1 min-h-[60px] max-h-[120px] px-4 py-3 border border-gray-300 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none bg-white dark:bg-gray-800"
                disabled={isLoading}
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="self-end"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
        </Card>

        {/* Info card */}
        <Card>
          <CardContent className="pt-6">
            <h3 className="font-semibold mb-2">How it works</h3>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>• This chatbot uses RAG (Retrieval-Augmented Generation) to answer questions</li>
              <li>• Responses are grounded in actual events and signposts from our database</li>
              <li>• A/B tier evidence moves our AGI proximity gauges, C/D tier is for context only</li>
              <li>• All sources are cited with similarity scores</li>
              <li>• Questions outside AGI/AI progress topics will be politely declined</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

