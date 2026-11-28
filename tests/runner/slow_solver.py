import time

def solve_slow(instance, config):
    time.sleep(60)

def solve_boom(instance, config):
    raise RuntimeError("license error giả lập")



def solve_checkpoint_slow(instance, config):
    """Ghi incumbent hợp lệ theo contract checkpoint, sau đó giả lập hard hang."""
    from src.common.checkpoint import write_incumbent_checkpoint
    from src.exact.oracle import solve_oracle

    result = solve_oracle(instance)
    assert result.solution is not None and result.lb is not None
    write_incumbent_checkpoint(
        instance,
        config,
        objective=result.lb,
        solution=result.solution,
        metrics={
            "t_encode": 0.1,
            "t_solve": 0.2,
            "t_total": 0.3,
            "variables": 4,
            "clauses": 3,
            "peak_memory": 12.5,
        },
    )
    time.sleep(60)



def solve_memory_hog(instance, config):
    """Cố cấp phát 192 MiB; nếu OS cap hoạt động, worker phải nhận MemoryError."""
    chunks = []
    for _ in range(24):
        chunks.append(bytearray(8 * 1024 * 1024))
    # Nếu giới hạn không được áp dụng, trả sai contract để test chắc chắn fail.
    from src.common.models import Result
    return Result(status="FEAS", lb=0, ub=instance.n - 1, solution=None)
