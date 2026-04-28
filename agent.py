import json
from openai import OpenAI
from tools import search_products, get_product, get_order, evaluate_return, tool_map,tools
client = OpenAI()


prompt = """
You are a retail AI assistant.

Rules:
- Never assume facts not present in the product data
- Only use the provided product fields (tags, title, etc.) to justify decisions
- Do not infer missing attributes

For product recommendations:
- Clearly explain why each product fits the user's constraints
- For each constraint:
  - If satisfied → explicitly state how
  - If not satisfied → explicitly state that it does not match
  - If data is missing or unclear → explicitly state uncertainty
  - Only state the attributes that are present in the product data
  -The result should be well structured without any extra symbols or information 
"""

def run_agent(user_input):
    mesgs = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_input}
    ]

    while True:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=mesgs,
            tools=tools,
            tool_choice="auto"
        )
        
        msg = res.choices[0].message

        # If tool call
        if msg.tool_calls:
            mesgs.append(msg)

            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                result = tool_map[name](**args)
                mesgs.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

        else:
            mesgs.append(msg)
            return msg.content




if __name__ == "__main__":
    print("\nRetail AI Assistant\n")

    while True:
        query = input("Customer: ")
        try:
            response = run_agent(query)
            print("\nAgent:", response, "\n")
        except Exception as e:
            print("Error:", str(e))