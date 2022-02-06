deno compile --unstable --allow-all --no-check \
    --target x86_64-unknown-linux-gnu -o host-manager-linux-x86_64 index.ts

deno compile --unstable --allow-all --no-check \
    --target x86_64-pc-windows-msvc -o host-manager-windows-x86_64 index.ts

deno compile --unstable --allow-all --no-check \
    --target x86_64-apple-darwin -o host-manager-darwin-x86_64 index.ts

deno compile --unstable --allow-all --no-check \
    --target aarch64-apple-darwin -o host-manager-darwin-aarch64 index.ts