"use client"

import { Button } from "@/components/ui/button"

interface FollowUpSuggestionsProps {
  suggestions: string[]
  onSuggestionClick: (suggestion: string) => void
}

export function FollowUpSuggestions({ suggestions, onSuggestionClick }: FollowUpSuggestionsProps) {
  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {suggestions.map((suggestion, index) => (
        <Button
          key={index}
          variant="outline"
          size="sm"
          onClick={() => onSuggestionClick(suggestion)}
          className="text-xs hover:bg-stone-700 hover:border-stone-600 bg-stone-800 border-stone-700 text-stone-300"
        >
          {suggestion}
        </Button>
      ))}
    </div>
  )
}
