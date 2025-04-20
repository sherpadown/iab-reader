FROM python:3.12.10-alpine AS builder

# prepare base system
COPY pyproject.toml /
COPY README.md /
COPY src/ /
RUN pip install .

# clean up (keep only bytecode)
# original code : https://github.com/CrafterKolyan/tiny-python-docker-image/blob/main/Dockerfile.scratch-full
WORKDIR /usr/local/lib/python3.12
RUN python -m compileall -o 2 .
RUN find . -name "*.cpython-*.opt-2.pyc" | awk '{print $1, $1}' | sed 's/__pycache__\///2' | sed 's/.cpython-[0-9]\{2,\}.opt-2//2' | xargs -n 2 mv
##RUN find . -mindepth 1 | grep -v -E '^\./(encodings)([/.].*)?$' | xargs rm -rf   # error runtime
RUN find . -name "*.py" -delete
RUN find . -name "__pycache__" -exec rm -r {} +


# build minimal image
FROM scratch
COPY --from=builder /usr/local/bin/python3.12          /usr/local/bin/python
COPY --from=builder /usr/local/lib/libpython3.12.so    /usr/local/lib/libpython3.12.so.1.0
COPY --from=builder /usr/local/lib/python3.12          /usr/local/lib/python3.12
COPY --from=builder /usr/lib/libz.so.1.3.1             /usr/lib/libz.so.1
COPY --from=builder /lib/ld-musl-x86_64.so.1           /lib/ld-musl-x86_64.so.1
COPY src/ /

ENTRYPOINT ["python", "-m", "iab_reader"]
