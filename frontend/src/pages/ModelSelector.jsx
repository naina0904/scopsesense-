import {
    Bot
} from "lucide-react";

function ModelSelector({
    provider,
    setProvider
}) {

    return (

        <div className="
            bg-slate-900
            border
            border-slate-800
            rounded-2xl
            p-6
        ">

            <div className="
                flex
                items-center
                gap-3
                mb-4
            ">

                <Bot className="text-indigo-400" />

                <h2 className="text-2xl font-semibold">

                    AI Model

                </h2>

            </div>

            <select
                value={provider}
                onChange={(e) =>
                    setProvider(
                        e.target.value
                    )
                }
                className="
                    w-full
                    bg-slate-800
                    border
                    border-slate-700
                    rounded-xl
                    p-4
                    text-white
                    outline-none
                "
            >

                <option value="groq">

                    Groq Llama 3

                </option>

                <option value="gemini">

                    Gemini Flash 2.5

                </option>

            </select>

        </div>
    );
}

export default ModelSelector;