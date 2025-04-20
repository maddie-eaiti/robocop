from google import genai
from google.genai import types
import base64

def generate(highlight: str, context: str, request: str) -> str:
  client = genai.Client(
      vertexai=True,
      project="gemini-api-testing-456915",
      location="us-central1",
  )

  highlight_block = f"The user has currently highlighted the text: \"{highlight}\"." if highlight else "The user currently does not have any text highlighted."
  msg1_text1 = types.Part.from_text(text=f"""You are a helpful assistant. You are given a highlight context and a request. {highlight_block}. The previous work they have done is: \"{context}\". Also attached is a screenshot which shows the work they are currently doing. The user has asked you to: \"{request}\". 

You are to respond with a JSON object that contains the text to be replaced as \"oldText\" and the rewritten text as \"newText\".""")


#   image1 = types.Part.from_bytes(
#       data=base64.b64decode(),
#       mime_type="image/png",
#   )

  model = "gemini-2.5-flash-preview-04-17"
  contents = [
    types.Content(
      role="user",
      parts=[
        msg1_text1
        # image1
      ]
    ),
  ]
  generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 0.95,
    max_output_tokens = 8192,
    response_modalities = ["TEXT"],
    safety_settings = [types.SafetySetting(
      category="HARM_CATEGORY_HATE_SPEECH",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_DANGEROUS_CONTENT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_HARASSMENT",
      threshold="OFF"
    )],
  )

  response = ""
  for chunk in client.models.generate_content_stream(
    model = model,
    contents = contents,
    config = generate_content_config,
    ):
    response += chunk.text
  return response