"use client";

import { useEffect,useRef,useState } from "react";
import { useAuth } from "react-oidc-context";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
};

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);


useEffect(() => {
  messagesEndRef.current?.scrollIntoView({
    behavior: "smooth",
    block: "end",
  });
}, [messages, loading]);
  async function handleSubmit() {
    if (!question.trim() || loading) {
      return;
    }

    const userQuestion = question.trim();

    setMessages((current) => [
      ...current,
      {
        role: "user",
        content: userQuestion,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: userQuestion,
          history: messages.map((message) =>({
            role: message.role,
            content:message.content,
          }))
        }),
      });

    if (!response.ok) {
  let errorMessage = "Unable to process the request.";

  try {
    const errorData = await response.json();

    if (
      typeof errorData.detail === "string" &&
      errorData.detail.trim()
    ) {
      errorMessage = errorData.detail;
    }
  } catch {
    // Keep the safe fallback message.
  }

  throw new Error(errorMessage);
    }

      const data = await response.json();

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources ?? [],
        },
      ]);
      } catch (error) {
  const errorMessage =
    error instanceof Error
      ? error.message
      : "Unable to get a response from the backend.";

  setMessages((currentMessages) => [
    ...currentMessages,
    {
      role: "assistant",
      content: errorMessage,
      sources: [],
    },
  ]);
  } finally {
      setLoading(false);
    }
  }
  return (
    <main className="flex min-h-screen bg-gray-100">
      <div className="mx-auto flex h-screen w-full max-w-4xl flex-col bg-white shadow">
        <header className="border-b px-6 py-4">
      <div className="flex items-center justify-between gap-4">
      <div>
        <h1 className="text-xl font-semibold">
          Clinical Laboratory AI Assistant
        </h1>

        <p className="mt-1 text-sm text-gray-500">
          Ask questions about laboratory tests, policies, and procedures.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-600">
        </span>

        <button
          type="button"
          onClick={async () => {

            const domain =
              process.env.NEXT_PUBLIC_COGNITO_DOMAIN;

            const clientId =
              process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID;

            const logoutUri =
              process.env.NEXT_PUBLIC_COGNITO_LOGOUT_URI;

            window.location.href =
              `${domain}/logout?client_id=${clientId}&logout_uri=${encodeURIComponent(
                logoutUri!
              )}`;
          }}
          className="rounded-lg border px-3 py-2 text-sm"
        >
          Sign out
        </button>
      </div>
    </div>
  </header>

        <section className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 && (
            <div className="flex h-full items-center justify-center">
              <div className="text-center text-gray-500">
                <p className="text-lg font-medium">
                  How can I help?
                </p>

                <p className="mt-2 text-sm">
                  Try asking: What specimen is used for CBC?
                </p>
              </div>
            </div>
          )}

          <div className="space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === "user"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                    message.role === "user"
                      ? "bg-black text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <p className="whitespace-pre-wrap">
                    {message.content}
                  </p>

                  {message.sources &&
                    message.sources.length > 0 && (
                      <div className="mt-3 border-t border-gray-300 pt-2 text-xs text-gray-600">
                        <p className="font-semibold">Sources</p>

                        {message.sources.map((source) => (
                          <p key={source}>{source}</p>
                        ))}
                      </div>
                    )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-2xl bg-gray-100 px-4 py-3 text-gray-500">
                  Thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </section>

        <footer className="border-t bg-white p-4">
          <div className="flex gap-3">
            <textarea
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey
                ) {
                  event.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder="Ask a laboratory question..."
              rows={2}
              className="flex-1 resize-none rounded-xl border bg-white px-4 py-3 text-black placeholder:text-gray-500 outline-none focus:ring-2"
            />
            <button
            type="button"
            onClick={handleSubmit}
            disabled={loading || !question.trim()}
            className="rounded-xl bg-gray-600 px-5 py-2 text-white hover:bg-gray-600 disabled:cursor-not-allowed disabled:bg-gray-400 disabled:text-gray-100"
            >
            {loading ? "Sending..." : "Send"}
          </button>
          </div>

          <p className="mt-2 text-center text-xs text-gray-400">
            For informational support only. Clinical decisions require qualified review.
          </p>
        </footer>
      </div>
    </main>
  );
}