import { type NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  try {
    const { messages, sessionId } = await req.json()
    const lastMessage = messages[messages.length - 1]

    // Prepare payload for langflow
    const payload = {
      input_value: lastMessage.content,
      output_type: "chat",
      input_type: "chat",
      session_id: sessionId || "user_1",
    }

    const options = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }

    // Call your langflow API
    const response = await fetch("http://localhost:7860/api/v1/run/2b1ef68b-9cf7-4bb6-b3d8-1a809a4e6070", options)
    const data = await response.json()

    // Extract the response text from langflow
    const responseText =
      data.outputs?.[0]?.outputs?.[0]?.results?.message?.text ||
      data.message ||
      "I'm sorry, I couldn't process that request."

    // Return simple JSON response for now
    return NextResponse.json({
      role: "assistant",
      content: responseText,
    })
  } catch (error) {
    console.error("Error calling langflow:", error)
    return NextResponse.json({ error: "Error processing request" }, { status: 500 })
  }
}
