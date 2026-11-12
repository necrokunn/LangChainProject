# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI


# load_dotenv()

# model=ChatOpenAI(
#     model_name="gpt-5.5",
#     temperature=0.7
# )    

# question = "How to swim?"

# response = model.invoke(question)

# print(response.content)

from dotenv import load_dotenv
from langchain import tools
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain.messages import HumanMessage, ToolMessage, SystemMessage

load_dotenv()


model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    timeout=30,
    max_retries=1,
)   

# question = "How to swim?"

# print("sending request to model...")

# response = model.invoke(question)

# print(response.content)

# system_message = SystemMessage(
#     content="You are a helpful assistant that translates English to Japanese als also provide a Romanized Japanese version."
# )

# human_message = HumanMessage(
#     content="Translate the following English text to Japanese: 'Hello, how are you?'"
# )

# messages = [system_message, human_message]

# model_response = model.invoke(messages)

# print(model_response.content)

# class TranslationOutput(BaseModel):
#     japanese: str = Field(..., description="The translated text in Japanese.")
#     romanized: str = Field(..., description="The Romanized version of the Japanese translation.")

# structured_prompt = model.with_structured_output(
#     output_schema=TranslationOutput,
# )

# response = structured_prompt.invoke(
#     "Translate the following English text to Japanese: 'Hello, how are you?'")

# print(response) 


class ShoppingResponse(BaseModel) :
    product_name: str = Field(description="Name of the recommended product")
    price: float = Field(description="Price of the product in USD")
    availability: str = Field(description="Whether the product is in stock, e.g. 'In stock' or 'Out of stock'")
    recommendation: str = Field(description="Short explanation of why this product fits the customer's request")
    next_action: str = Field(description="What the customer should do next, e.g. 'Add to cart'")

PRODUCTS ={ 
    "LAP001": { 
        "name": "Swifteook Air 14",
        "price": 899,
        "category": "laptop",
        "in_stock": True,
        "specs": {"ram": "16GB", "storage": "512GB SSD", "processor": "Intel Core i5", "screen": "14-inch"}
    },
    "LAP002": {
        "name": "StudyMate 15",
        "price": 649,
        "category": "laptop",
        "in_stock": True,
        "specs": {"ram": "8GB", "storage": "256GB SSD", "processor": "AMD Ryzen 5", "screen": "15.6-inch"}
    },
    "LAP003": {
        "name": "ProEdge X16",
        "price": 1499, 
        "category": "laptop",
        "in_stock": False,
        "specs": {"ram": "32GB", "storage": "1TB SSD", "processor": "Intel Core i7", "screen": "16-inch"}
    },  
    "PHN001": {
        "name": "Nova Phone 12",
        "price": 599,
        "category": "phone",
        "in_stock": True,
        "specs": {"storage": "128GB", "camera": "50MP", "screen": "6.5-inch"},
    },
    "AUD001": {
        "name": "QuietWave Headphones",
        "price": 149,
        "category": "headphones",
        "in_stock": True,
        "specs": {"type": "over-ear", "noise_cancelling": "yes", "battery": "30 hours"},
        }
}

STORE_INFO = {
    "return_policy": "Items can be returned within 30 days of delivery in original condition for a full refund.",
    "shipping_policy": "Standard shipping takes 3-5 business days. Free shipping on orders over $50.",
    "late_order_policy": "If an order is more than 3 days past its expected delivery date, contact support for a replacement or refund.",
    "support_contact": "support@example-shop.com",
}

ORDERS = {
    "ORD1001": "Shipped",
    "ORD1002": "Processing",
    "ORD1003": "Delivered",
    "ORD1004": "Delayed",
}

@tool
def search_products(query: str) -> str:
    """This function searches for products based on the query and returns a formatted string of matching products."""
    words = query.lower().split()
    max_price = None
    if "under" in words:
        index = words.index("under")
        if index + 1 < len(words):
            price_str = words[index + 1].strip("$,.").replace(",", "")
            if price_str.isdigit():
                max_price = float(price_str)


    matching_products = []
    for product in PRODUCTS.values():
        if any(word in product["name"].lower() for word in words) and (max_price is None or product["price"] <= max_price):
                    matching_products.append(product)

    return str(matching_products) if matching_products else "No matching products found."

# answer = search_products.invoke("I am looking for a laptop under $1000 with at least 16GB RAM. Can you recommend one?")
# print('Here is the answer to your query:')
# print(answer)

@tool
def check_order_status(order_id: str) -> str:
    """This function checks the status of an order based on the order ID."""
    order_id = order_id.strip().upper()
    if order_id in ORDERS:
        return f"The status of order {order_id} is: {ORDERS[order_id]}."
    else:
        return f"No order found with ID {order_id}."                

    print(check_order_status.invoke("ORD1001"))

# linking and binding tools
tools = [search_products, check_order_status]   
model_with_tools = model.bind_tools(tools)                    

messages = [HumanMessage(content="Where is my order ORD1001?")]

response = model_with_tools.invoke(messages)

# print("Model With Response: ", response)
# print("Tool calls: ", response.tool_calls)

messages.append(response)

for tool_call in response.tool_calls:
    if tool_call["name"] == "check_order_status":
          tool_result = check_order_status.invoke(tool_call["args"])
    elif tool_call["name"] == "search_products":
        tool_result = search_products.invoke(tool_call["args"])
    else:
        continue

messages.append(ToolMessage
                (content=tool_result,
                tool_call_id=tool_call["id"]
                ))

final_response = model_with_tools.invoke(messages)

print("Final Response: ", final_response.content)