from __future__ import annotations

import os
from typing import Any

# Nạp biến môi trường từ .env (LANGFUSE_PUBLIC_KEY/SECRET_KEY/HOST...) nếu có.
try:  # pragma: no cover
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass

# Langfuse Python SDK v3: `observe` + `get_client` import ở top-level
# (v2 cũ dùng `langfuse.decorators` + `langfuse_context` — đã bỏ ở v3).
# Lớp shim dưới đây giữ nguyên API mà app/agent.py đang gọi
# (`langfuse_context.update_current_trace / update_current_observation`)
# nhưng map sang API v3, nên không phải sửa agent.py.
try:
    from langfuse import get_client, observe  # type: ignore

    class _ContextShim:
        """Cầu nối API v2-style mà agent.py dùng -> Langfuse v3."""

        def update_current_trace(self, **kwargs: Any) -> None:
            try:
                get_client().update_current_trace(**kwargs)
            except Exception:  # pragma: no cover - không để tracing làm sập request
                pass

        def update_current_observation(
            self,
            metadata: Any | None = None,
            usage_details: Any | None = None,
            **kwargs: Any,
        ) -> None:
            try:
                client = get_client()
                if metadata is not None:
                    client.update_current_span(metadata=metadata)
                if usage_details is not None:
                    # usage chỉ gắn được vào observation kiểu generation;
                    # bọc try riêng để span thường không bị lỗi.
                    try:
                        client.update_current_generation(usage_details=usage_details)
                    except Exception:
                        pass
            except Exception:  # pragma: no cover
                pass

    langfuse_context = _ContextShim()

except Exception:  # pragma: no cover - chưa cài langfuse: dùng no-op
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

    langfuse_context = _DummyContext()


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
