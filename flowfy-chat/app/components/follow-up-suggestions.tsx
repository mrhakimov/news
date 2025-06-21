"use client"

import { Button } from "@/components/ui/button"

interface FollowUpSuggestionsProps {
  suggestions: string[]
  onSuggestionClick: (suggestion: string) => void
}

export function FollowUpSuggestions({ suggestions, onSuggestionClick }: FollowUpSuggestionsProps) {
  return (
    <div className="grid grid-cols-2 gap-3 mt-4">
      {suggestions.map((suggestion, index) => (
        <Button
          key={index}
          variant="outline"
          onClick={() => onSuggestionClick(suggestion)}
          className="h-12 text-[11px] leading-tight px-4 py-2 hover:bg-stone-700 hover:border-stone-600 bg-stone-800 border-stone-700 text-stone-300 text-center justify-center overflow-hidden text-ellipsis line-clamp-2"
        >
          {suggestion}
        </Button>
      ))}
    </div>
  )
}
