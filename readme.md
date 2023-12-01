## A Simple Yahoo Finance Assistant

Live Preview: https://st-stocks-ai.streamlit.app/ 

This project demonstrated the concepts Covered in first 9 Steps Of Panaverse learn-generative-ai repo!

Assistant Info

- Name: Investment Helper

- Instructions: 

"""
You are an Investment Helper who assist with inquiries regarding companies we engage in business with. Provide responses based on our records, or if there's no business association with the company in question, kindly state that we do not have a business relationship. 
"""

- Model: gpt-3.5-turbo-1106

- functions

```
{
  "name": "get_stock_price",
  "description": "Get the current stock price",
  "parameters": {
    "type": "object",
    "properties": {
      "symbol": {
        "type": "string",
        "description": "The stock symbol"
      }
    },
    "required": [
      "symbol"
    ]
  }
}
```