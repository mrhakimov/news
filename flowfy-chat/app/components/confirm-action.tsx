"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, X, AlertTriangle } from "lucide-react"
import { MarkdownRenderer } from "./markdown-renderer"

interface ConfirmActionProps {
  action: string
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmAction({ action, onConfirm, onCancel }: ConfirmActionProps) {
  return (
    <Card className="border-orange-600 bg-orange-900/20">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base text-white">
          <AlertTriangle className="w-4 h-4 text-orange-400" />
          Confirmation Required
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-sm">
          <MarkdownRenderer content={action} />
        </div>
        <div className="flex gap-2">
          <Button onClick={onConfirm} size="sm" className="bg-green-600 hover:bg-green-700">
            <CheckCircle className="w-4 h-4 mr-1" />
            Confirm
          </Button>
          <Button
            onClick={onCancel}
            variant="outline"
            size="sm"
            className="border-stone-600 text-stone-300 hover:bg-stone-700"
          >
            <X className="w-4 h-4 mr-1" />
            Cancel
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
