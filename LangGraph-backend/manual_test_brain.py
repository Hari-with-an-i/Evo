import sys
import os
from dotenv import load_dotenv

# Ensure we can import from app
sys.path.append(os.getcwd())

load_dotenv()

try:
    from app.brain import brain_app
    from langchain_core.messages import HumanMessage
except ImportError as e:
    print(f"Import Error: {e}")
    print("Make sure you are running this from the LangGraph-backend directory.")
    sys.exit(1)

def main():
    print("==================================================")
    print("   🤖 Dynamic Brain - Manual Test Console")
    print("==================================================")
    print("Type your query below. Type 'exit' or 'quit' to stop.")
    print("--------------------------------------------------")

    while True:
        try:
            query = input("\n🧑 User: ").strip()
        except EOFError:
            break
            
        if query.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
            
        if not query:
            continue
            
        print("\n⏳ Agent is thinking...")
        
        try:
            initial_state = {"messages": [HumanMessage(content=query)]}
            
            # Use stream to show progress in real-time
            # stream_mode="values" yields the full state at each step
            # stream_mode="updates" yields only the updates
            
            final_response = ""
            
            for event in brain_app.stream(initial_state, stream_mode="updates"):
                # event is a dict like {'agent': {'messages': [...]}} or {'tools': {'messages': [...]}}
                
                for node_name, node_update in event.items():
                    if "messages" in node_update:
                        messages = node_update["messages"]
                        # messages is usually a list of new messages added in this step
                        
                        for msg in messages:
                            # 1. Agent decides to call a tool
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    print(f"  🛠️  [CALLING TOOL]: {tc['name']}")
                                    print(f"     args: {tc['args']}")
                            
                            # 2. Tool Output
                            if msg.type == 'tool':
                                # Truncate long outputs for readability
                                content_preview = str(msg.content)[:300].replace('\n', ' ')
                                print(f"  📥  [TOOL OUTPUT]: {content_preview}...")
                            
                            # 3. Final AI Response (or intermediate thought)
                            if msg.type == 'ai' and not msg.tool_calls:
                                final_response = msg.content
            
            # Print the final response clearly at the end
            if final_response:
                print(f"\n🤖 Agent: {final_response}")
            else:
                 # Should have been caught in the loop, but just in case
                 print("\n(No text response - maybe just tool calls)")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
