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
    const response = await fetch("http://localhost:7868/api/v1/run/09d604c2-99a3-4c1e-9517-082bc7960038", options)
    const data = await response.json()
    // console.log("=== LANGFLOW DATA ===")
    // console.log(JSON.stringify(data, null, 2))
    // console.log("=== END LANGFLOW DATA ===")
    // Extract the response text from langflow
    let responseText = "I'm sorry, I couldn't process that request."
    let suggestions = []

    try {
      const rawText = data.outputs?.[0]?.outputs?.[0]?.results?.message?.text || data.message
      
      if (rawText) {
        // Parse the stringified JSON from langflow
        const parsedData = JSON.parse(rawText)
        console.log("=== PARSED LANGFLOW DATA ===")
        console.log(JSON.stringify(parsedData, null, 2))
        console.log("=== END PARSED DATA ===")
        
        if (parsedData.results && parsedData.results.length > 0) {
          responseText = parsedData.results[0].response || responseText
          suggestions = parsedData.results[0].metadata?.suggestions || []
        }
      }
    } catch (parseError) {
      console.error("Error parsing langflow response:", parseError)
      // Fallback to raw text if parsing fails
      responseText = data.outputs?.[0]?.outputs?.[0]?.results?.message?.text || data.message || responseText
    }

    // Return response with suggestions
    return NextResponse.json({
      role: "assistant",
      content: responseText,
      suggestions: suggestions,
    })
  } catch (error) {
    console.error("Error calling langflow:", error)
    return NextResponse.json({ error: "Error processing request" }, { status: 500 })
  }
}
