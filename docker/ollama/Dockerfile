FROM ollama/ollama:latest

COPY docker/ollama/start-ollama.sh /usr/local/bin/start-ollama.sh
RUN sed -i 's/\r$//' /usr/local/bin/start-ollama.sh \
	&& chmod +x /usr/local/bin/start-ollama.sh

ENTRYPOINT ["/bin/sh", "/usr/local/bin/start-ollama.sh"]
