FROM alpine:3.19

RUN echo "Django for OdyseeHAUMere" \
	&& apk -U upgrade \
	&& apk add --no-cache tzdata python3 py3-pip \
	&& pip3 install --no-cache-dir --break-system-packages django djangorestframework

CMD ["/persist/app.sh"]
