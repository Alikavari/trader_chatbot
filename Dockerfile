FROM python:3.12
RUN pip install uv
RUN --mount=source=dist,target=/dist uv pip install --no-cache --system /dist/*.whl
WORKDIR /app
COPY ./prompts/prompt.txt ./prompts/prompt.txt
# CMD python -m
# CMD fastapi run trader_chatbot/main.py
ENV TERM=xterm
EXPOSE 8000
CMD muon-chatbot
