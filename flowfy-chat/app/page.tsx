"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Send, User } from "lucide-react"
import { FinancialChart } from "./components/financial-chart"
import { FollowUpSuggestions } from "./components/follow-up-suggestions"
import { ConfirmAction } from "./components/confirm-action"
import { MarkdownRenderer } from "./components/markdown-renderer"

// Add ThinkingTimer component before the main component
const ThinkingTimer = ({ startTime }: { startTime: number }) => {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    return () => clearInterval(interval)
  }, [startTime])

  return (
    <span className="text-xs text-gray-500 ml-auto">{elapsed}s</span>
  )
}

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
}

export default function ChatPage() {
  const [sessionId] = useState(() => `user_${Date.now()}`)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [loadingStartTime, setLoadingStartTime] = useState(0)
  const [showChart, setShowChart] = useState(false)
  const [chartData, setChartData] = useState<any[]>([])
  const [pendingAction, setPendingAction] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)
    setLoadingStartTime(Date.now())

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          sessionId,
        }),
      })

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.content,
      }

      setMessages((prev) => [...prev, assistantMessage])

      // Check if response contains financial data or action requests
      const content = data.content.toLowerCase()

      if (content.includes("portfolio") || content.includes("investment") || content.includes("stock")) {
        const sampleData = [
          { name: "Jan", value: 4000, growth: 2400 },
          { name: "Feb", value: 3000, growth: 1398 },
          { name: "Mar", value: 2000, growth: 9800 },
          { name: "Apr", value: 2780, growth: 3908 },
          { name: "May", value: 1890, growth: 4800 },
          { name: "Jun", value: 2390, growth: 3800 },
        ]
        setChartData(sampleData)
        setShowChart(true)
      }

      if (content.includes("confirm") || content.includes("execute") || content.includes("proceed")) {
        setPendingAction(data.content)
      }
    } catch (error) {
      console.error("Error:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const followUpSuggestions = [
    "Show me my portfolio performance",
    "What are the latest market trends?",
    "Analyze my investment risk",
    "Suggest budget optimizations",
  ]

  const handleFollowUp = async (suggestion: string) => {
    if (isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: suggestion,
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    setLoadingStartTime(Date.now())

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          sessionId,
        }),
      })

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.content,
      }

      setMessages((prev) => [...prev, assistantMessage])

      // Check if response contains financial data or action requests
      const content = data.content.toLowerCase()

      if (content.includes("portfolio") || content.includes("investment") || content.includes("stock")) {
        const sampleData = [
          { name: "Jan", value: 4000, growth: 2400 },
          { name: "Feb", value: 3000, growth: 1398 },
          { name: "Mar", value: 2000, growth: 9800 },
          { name: "Apr", value: 2780, growth: 3908 },
          { name: "May", value: 1890, growth: 4800 },
          { name: "Jun", value: 2390, growth: 3800 },
        ]
        setChartData(sampleData)
        setShowChart(true)
      }

      if (content.includes("confirm") || content.includes("execute") || content.includes("proceed")) {
        setPendingAction(data.content)
      }
    } catch (error) {
      console.error("Error:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfirmAction = () => {
    setPendingAction(null)
    const confirmMessage: Message = {
      id: Date.now().toString(),
      role: "assistant",
      content: "✅ Action confirmed and executed successfully.",
    }
    setMessages((prev) => [...prev, confirmMessage])
  }

  return (
    <div className="flex flex-col h-screen bg-stone-950">
      {/* Header */}
      <div className="border-b border-stone-800 bg-stone-900 px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold text-white">flowfy</h1>
          <p className="text-sm text-gray-400">Your AI Financial Assistant</p>
        </div>
      </div>

      {/* Chat Messages */}
      <ScrollArea className="flex-1 px-6 py-4 bg-stone-950" ref={scrollAreaRef}>
        <div className="space-y-6 max-w-4xl mx-auto">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <h2 className="text-xl font-semibold text-white mb-2">Welcome to flowfy</h2>
              <p className="text-gray-400 mb-6">
                Your AI-powered financial assistant. Ask me about your finances, investments, or market trends.
              </p>
              <FollowUpSuggestions suggestions={followUpSuggestions} onSuggestionClick={handleFollowUp} />
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id} className="flex gap-4">
              <Avatar className="w-8 h-8 mt-1">
                <AvatarFallback
                  className={message.role === "user" ? "bg-stone-600 text-white" : "bg-gray-700 text-white"}
                >
                  {message.role === "user" ? (
                    <User className="w-4 h-4" />
                  ) : (
                    <span className="font-bold text-xs">F</span>
                  )}
                </AvatarFallback>
              </Avatar>

              <div className="flex-1 space-y-3">
                <Card
                  className={`${message.role === "user" ? "bg-stone-800/50 border-stone-700" : "bg-stone-800 border-stone-700"}`}
                >
                  <CardContent className="p-4">
                    <MarkdownRenderer content={message.content} />
                  </CardContent>
                </Card>

                {/* Show chart if this is the last AI message and chart should be shown */}
                {message.role === "assistant" && message.id === messages[messages.length - 1]?.id && showChart && (
                  <FinancialChart data={chartData} />
                )}

                {/* Show confirm action if this is the last AI message and there's a pending action */}
                {message.role === "assistant" && message.id === messages[messages.length - 1]?.id && pendingAction && (
                  <ConfirmAction
                    action={pendingAction}
                    onConfirm={handleConfirmAction}
                    onCancel={() => setPendingAction(null)}
                  />
                )}

                {/* Show follow-up suggestions for the last AI message */}
                {message.role === "assistant" && message.id === messages[messages.length - 1]?.id && !isLoading && (
                  <FollowUpSuggestions suggestions={followUpSuggestions} onSuggestionClick={handleFollowUp} />
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-4">
              <Avatar className="w-8 h-8 mt-1">
                <AvatarFallback className="bg-gray-700 text-white">
                  <span className="font-bold text-xs">F</span>
                </AvatarFallback>
              </Avatar>
              <Card className="flex-1 bg-stone-800 border-stone-700">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.1s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-400">flowfy is thinking...</span>
                    </div>
                    <ThinkingTimer startTime={loadingStartTime} />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-stone-800 bg-stone-900 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me about your finances, investments, or market trends..."
              className="flex-1 bg-stone-800 border-stone-700 text-white placeholder:text-gray-400"
              disabled={isLoading}
            />
            <Button type="submit" disabled={isLoading || !input.trim()} className="bg-stone-600 hover:bg-stone-700">
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
