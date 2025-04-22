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

def help_transcribe(transcription: str, screenshot_path: str) -> str:
  print("Transcription: ", transcription)
  client = genai.Client(
      vertexai=True,
      project="gemini-api-testing-456915",
      location="us-central1",
  )

  msg1_text1 = types.Part.from_text(text=f"""You are a helpful assistant. The user is attempting to transcribe their speech to text, though the transcription does not always work perfectly. It can mishear words, or sometimes, words can be missed entirely. Provided is a screenshot of the user's screen, which shows the work they are currently doing. Please help use this to figure out what words were missed or misheard. Sometimes, what the user intended to be a symbol could be recorded as a word instead, so be sure to stay on the lookout for that. Make sure to always return a result with contextually logical grammar, syntax and punctuation; and feel free to add punctuation like semicolons, quotation marks, or others where if it is appropriate (which it may not always be). Do not attempt to reword, and absolutely do not try to copy edit or improve the user's speech.
Here is the generated transcription of the user's speech: \"{transcription}\". 

Respond with only the corrected transcription, and do NOT include any other text, explanation, or description of what you are returning.""")
  with open(screenshot_path, "rb") as f:
      image_bytes = f.read()

  image1 = types.Part.from_bytes(
      data=image_bytes,
      mime_type="image/png"
  )

  model = "gemini-2.0-flash-001"
  contents = [
    types.Content(
      role="user",
      parts=[
        msg1_text1,
        image1
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