### SYSTEM ERROR DETECTED FOR FIXING

Context: Dashboard Load
Error Type: MemoryError
Error: Unable to allocate 1.06 MiB for an array with shape (138388,) and data type uint64
Timestamp: 2026-04-05 15:37:12

Environment:
```json
{
  "python": "3.14.3",
  "platform": "Windows-11-10.0.26200-SP0",
  "cwd": "H:\\Analysis\\Automation-Pivot"
}
```

Additional Details:
```json
{}
```

Traceback:
```python
Traceback (most recent call last):
  File "H:\Analysis\Automation-Pivot\FrontEnd\pages\dashboard.py", line 260, in render_dashboard_tab
    df_woo_only = ensure_sales_schema(
        load_hybrid_data(
    ...<5 lines>...
        )
    )
  File "H:\Analysis\Automation-Pivot\BackEnd\utils\sales_schema.py", line 85, in ensure_sales_schema
    out["customer_key"] = out["customer_key"].fillna("").astype(str).str.strip().str.lower()
                          ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^
  File "C:\Users\deenb\AppData\Roaming\Python\Python314\site-packages\pandas\core\generic.py", line 7372, in fillna
    new_data = self._mgr.fillna(
        value=value, limit=limit, inplace=inplace, downcast=downcast
    )
  File "C:\Users\deenb\AppData\Roaming\Python\Python314\site-packages\pandas\core\internals\base.py", line 186, in fillna
    return self.apply_with_block(
           ~~~~~~~~~~~~~~~~~~~~~^
        "fillna",
        ^^^^^^^^^
    ...<5 lines>...
        already_warned=_AlreadyWarned(),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\Users\deenb\AppData\Roaming\Python\Python314\site-packages\pandas\core\internals\managers.py", line 363, in apply
    applied = getattr(b, f)(**kwargs)
  File "C:\Users\deenb\AppData\Roaming\Python\Python314\site-packages\pandas\core\internals\blocks.py", line 1743, in fillna
    nbs = nb._maybe_downcast(
        [nb], downcast=downcast, using_cow=using_cow, caller="fillna"
    )
  File "C:\Users\deenb\AppData\Roaming\Python\Python314\site-packages\pandas\core\internals\blocks.py", line 567, in _maybe_downcast
    blk.convert(
    ~~~~~~~~~~~^
        using_cow=using_cow, copy=not using_cow, convert_string=False
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\Users\deenb\AppData\Roaming\Python\Python314\site-packages\pandas\core\internals\blocks.py", line 675, in convert
    res_values = lib.maybe_convert_objects(
        values,  # type: ignore[arg-type]
        convert_non_numeric=True,
        convert_string=convert_string,
    )
  File "pandas/_libs/lib.pyx", line 2558, in pandas._libs.lib.maybe_convert_objects
numpy._core._exceptions._ArrayMemoryError: Unable to allocate 1.06 MiB for an array with shape (138388,) and data type uint64

```

Task:
1. Explain the likely root cause.
2. Identify the safest code change.
3. Suggest tests to prevent regression.
4. Mention any schema mismatch, missing secret, or data-quality issue involved.
