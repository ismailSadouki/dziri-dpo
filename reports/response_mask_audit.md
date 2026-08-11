# Response Mask Audit

Model: `Qwen/Qwen2.5-0.5B-Instruct`

The audit verifies that prompt tokens receive `mask=0` and response tokens receive `mask=1`.

## Example: tiny_001

### Raw example

**Prompt**

```text
What is 2 + 2?
```

**Chosen**

```text
2 + 2 equals 4.
```

**Rejected**

```text
2 + 2 equals 5.
```

### Chosen response boundary

- `response_start`: `37`
- sequence length: `47`

```text
pos  | region | token_id | decoded
-----|--------|----------|--------
0000 | P | 151644 | '<|im_start|>'
0001 | P |   8948 | 'system'
0002 | P |    198 | '\\n'
0003 | P |   2610 | 'You'
0004 | P |    525 | ' are'
0005 | P |   1207 | ' Q'
0006 | P |  16948 | 'wen'
0007 | P |     11 | ','
0008 | P |   3465 | ' created'
0009 | P |    553 | ' by'
0010 | P |  54364 | ' Alibaba'
0011 | P |  14817 | ' Cloud'
0012 | P |     13 | '.'
0013 | P |   1446 | ' You'
0014 | P |    525 | ' are'
0015 | P |    264 | ' a'
0016 | P |  10950 | ' helpful'
0017 | P |  17847 | ' assistant'
0018 | P |     13 | '.'
0019 | P | 151645 | '<|im_end|>'
0020 | P |    198 | '\\n'
0021 | P | 151644 | '<|im_start|>'
0022 | P |    872 | 'user'
0023 | P |    198 | '\\n'
0024 | P |   3838 | 'What'
0025 | P |    374 | ' is'
0026 | P |    220 | ' '
0027 | P |     17 | '2'
0028 | P |    488 | ' +'
0029 | P |    220 | ' '
0030 | P |     17 | '2'
0031 | P |     30 | '?'
0032 | P | 151645 | '<|im_end|>'
0033 | P |    198 | '\\n'
0034 | P | 151644 | '<|im_start|>'
0035 | P |  77091 | 'assistant'
0036 | P |    198 | '\\n'
0037 | R |     17 | '2'
0038 | R |    488 | ' +'
0039 | R |    220 | ' '
0040 | R |     17 | '2'
0041 | R |  16819 | ' equals'
0042 | R |    220 | ' '
0043 | R |     19 | '4'
0044 | R |     13 | '.'
0045 | R | 151645 | '<|im_end|>'
0046 | R |    198 | '\\n'
```

### Rejected response boundary

- `response_start`: `37`
- sequence length: `47`

```text
pos  | region | token_id | decoded
-----|--------|----------|--------
0000 | P | 151644 | '<|im_start|>'
0001 | P |   8948 | 'system'
0002 | P |    198 | '\\n'
0003 | P |   2610 | 'You'
0004 | P |    525 | ' are'
0005 | P |   1207 | ' Q'
0006 | P |  16948 | 'wen'
0007 | P |     11 | ','
0008 | P |   3465 | ' created'
0009 | P |    553 | ' by'
0010 | P |  54364 | ' Alibaba'
0011 | P |  14817 | ' Cloud'
0012 | P |     13 | '.'
0013 | P |   1446 | ' You'
0014 | P |    525 | ' are'
0015 | P |    264 | ' a'
0016 | P |  10950 | ' helpful'
0017 | P |  17847 | ' assistant'
0018 | P |     13 | '.'
0019 | P | 151645 | '<|im_end|>'
0020 | P |    198 | '\\n'
0021 | P | 151644 | '<|im_start|>'
0022 | P |    872 | 'user'
0023 | P |    198 | '\\n'
0024 | P |   3838 | 'What'
0025 | P |    374 | ' is'
0026 | P |    220 | ' '
0027 | P |     17 | '2'
0028 | P |    488 | ' +'
0029 | P |    220 | ' '
0030 | P |     17 | '2'
0031 | P |     30 | '?'
0032 | P | 151645 | '<|im_end|>'
0033 | P |    198 | '\\n'
0034 | P | 151644 | '<|im_start|>'
0035 | P |  77091 | 'assistant'
0036 | P |    198 | '\\n'
0037 | R |     17 | '2'
0038 | R |    488 | ' +'
0039 | R |    220 | ' '
0040 | R |     17 | '2'
0041 | R |  16819 | ' equals'
0042 | R |    220 | ' '
0043 | R |     20 | '5'
0044 | R |     13 | '.'
0045 | R | 151645 | '<|im_end|>'
0046 | R |    198 | '\\n'
```

## Example: tiny_002

### Raw example

**Prompt**

```text
What is the capital of France?
```

**Chosen**

```text
The capital of France is Paris.
```

**Rejected**

```text
The capital of France is Berlin.
```

### Chosen response boundary

- `response_start`: `36`
- sequence length: `45`

```text
pos  | region | token_id | decoded
-----|--------|----------|--------
0000 | P | 151644 | '<|im_start|>'
0001 | P |   8948 | 'system'
0002 | P |    198 | '\\n'
0003 | P |   2610 | 'You'
0004 | P |    525 | ' are'
0005 | P |   1207 | ' Q'
0006 | P |  16948 | 'wen'
0007 | P |     11 | ','
0008 | P |   3465 | ' created'
0009 | P |    553 | ' by'
0010 | P |  54364 | ' Alibaba'
0011 | P |  14817 | ' Cloud'
0012 | P |     13 | '.'
0013 | P |   1446 | ' You'
0014 | P |    525 | ' are'
0015 | P |    264 | ' a'
0016 | P |  10950 | ' helpful'
0017 | P |  17847 | ' assistant'
0018 | P |     13 | '.'
0019 | P | 151645 | '<|im_end|>'
0020 | P |    198 | '\\n'
0021 | P | 151644 | '<|im_start|>'
0022 | P |    872 | 'user'
0023 | P |    198 | '\\n'
0024 | P |   3838 | 'What'
0025 | P |    374 | ' is'
0026 | P |    279 | ' the'
0027 | P |   6722 | ' capital'
0028 | P |    315 | ' of'
0029 | P |   9625 | ' France'
0030 | P |     30 | '?'
0031 | P | 151645 | '<|im_end|>'
0032 | P |    198 | '\\n'
0033 | P | 151644 | '<|im_start|>'
0034 | P |  77091 | 'assistant'
0035 | P |    198 | '\\n'
0036 | R |    785 | 'The'
0037 | R |   6722 | ' capital'
0038 | R |    315 | ' of'
0039 | R |   9625 | ' France'
0040 | R |    374 | ' is'
0041 | R |  12095 | ' Paris'
0042 | R |     13 | '.'
0043 | R | 151645 | '<|im_end|>'
0044 | R |    198 | '\\n'
```

### Rejected response boundary

- `response_start`: `36`
- sequence length: `45`

```text
pos  | region | token_id | decoded
-----|--------|----------|--------
0000 | P | 151644 | '<|im_start|>'
0001 | P |   8948 | 'system'
0002 | P |    198 | '\\n'
0003 | P |   2610 | 'You'
0004 | P |    525 | ' are'
0005 | P |   1207 | ' Q'
0006 | P |  16948 | 'wen'
0007 | P |     11 | ','
0008 | P |   3465 | ' created'
0009 | P |    553 | ' by'
0010 | P |  54364 | ' Alibaba'
0011 | P |  14817 | ' Cloud'
0012 | P |     13 | '.'
0013 | P |   1446 | ' You'
0014 | P |    525 | ' are'
0015 | P |    264 | ' a'
0016 | P |  10950 | ' helpful'
0017 | P |  17847 | ' assistant'
0018 | P |     13 | '.'
0019 | P | 151645 | '<|im_end|>'
0020 | P |    198 | '\\n'
0021 | P | 151644 | '<|im_start|>'
0022 | P |    872 | 'user'
0023 | P |    198 | '\\n'
0024 | P |   3838 | 'What'
0025 | P |    374 | ' is'
0026 | P |    279 | ' the'
0027 | P |   6722 | ' capital'
0028 | P |    315 | ' of'
0029 | P |   9625 | ' France'
0030 | P |     30 | '?'
0031 | P | 151645 | '<|im_end|>'
0032 | P |    198 | '\\n'
0033 | P | 151644 | '<|im_start|>'
0034 | P |  77091 | 'assistant'
0035 | P |    198 | '\\n'
0036 | R |    785 | 'The'
0037 | R |   6722 | ' capital'
0038 | R |    315 | ' of'
0039 | R |   9625 | ' France'
0040 | R |    374 | ' is'
0041 | R |  19846 | ' Berlin'
0042 | R |     13 | '.'
0043 | R | 151645 | '<|im_end|>'
0044 | R |    198 | '\\n'
```

## Example: tiny_003

### Raw example

**Prompt**

```text
Give me a short definition of a neural network.
```

**Chosen**

```text
A neural network is a model made of interconnected layers that learn patterns from data.
```

**Rejected**

```text
A neural network is a type of database used to store internet pages.
```

### Chosen response boundary

- `response_start`: `39`
- sequence length: `57`

```text
pos  | region | token_id | decoded
-----|--------|----------|--------
0000 | P | 151644 | '<|im_start|>'
0001 | P |   8948 | 'system'
0002 | P |    198 | '\\n'
0003 | P |   2610 | 'You'
0004 | P |    525 | ' are'
0005 | P |   1207 | ' Q'
0006 | P |  16948 | 'wen'
0007 | P |     11 | ','
0008 | P |   3465 | ' created'
0009 | P |    553 | ' by'
0010 | P |  54364 | ' Alibaba'
0011 | P |  14817 | ' Cloud'
0012 | P |     13 | '.'
0013 | P |   1446 | ' You'
0014 | P |    525 | ' are'
0015 | P |    264 | ' a'
0016 | P |  10950 | ' helpful'
0017 | P |  17847 | ' assistant'
0018 | P |     13 | '.'
0019 | P | 151645 | '<|im_end|>'
0020 | P |    198 | '\\n'
0021 | P | 151644 | '<|im_start|>'
0022 | P |    872 | 'user'
0023 | P |    198 | '\\n'
0024 | P |  35127 | 'Give'
0025 | P |    752 | ' me'
0026 | P |    264 | ' a'
0027 | P |   2805 | ' short'
0028 | P |   7271 | ' definition'
0029 | P |    315 | ' of'
0030 | P |    264 | ' a'
0031 | P |  29728 | ' neural'
0032 | P |   3922 | ' network'
0033 | P |     13 | '.'
0034 | P | 151645 | '<|im_end|>'
0035 | P |    198 | '\\n'
0036 | P | 151644 | '<|im_start|>'
0037 | P |  77091 | 'assistant'
0038 | P |    198 | '\\n'
0039 | R |     32 | 'A'
0040 | R |  29728 | ' neural'
0041 | R |   3922 | ' network'
0042 | R |    374 | ' is'
0043 | R |    264 | ' a'
0044 | R |   1614 | ' model'
0045 | R |   1865 | ' made'
0046 | R |    315 | ' of'
0047 | R |  82316 | ' interconnected'
0048 | R |  13617 | ' layers'
0049 | R |    429 | ' that'
0050 | R |   3960 | ' learn'
0051 | R |  12624 | ' patterns'
0052 | R |    504 | ' from'
0053 | R |    821 | ' data'
0054 | R |     13 | '.'
0055 | R | 151645 | '<|im_end|>'
0056 | R |    198 | '\\n'
```

### Rejected response boundary

- `response_start`: `39`
- sequence length: `55`

```text
pos  | region | token_id | decoded
-----|--------|----------|--------
0000 | P | 151644 | '<|im_start|>'
0001 | P |   8948 | 'system'
0002 | P |    198 | '\\n'
0003 | P |   2610 | 'You'
0004 | P |    525 | ' are'
0005 | P |   1207 | ' Q'
0006 | P |  16948 | 'wen'
0007 | P |     11 | ','
0008 | P |   3465 | ' created'
0009 | P |    553 | ' by'
0010 | P |  54364 | ' Alibaba'
0011 | P |  14817 | ' Cloud'
0012 | P |     13 | '.'
0013 | P |   1446 | ' You'
0014 | P |    525 | ' are'
0015 | P |    264 | ' a'
0016 | P |  10950 | ' helpful'
0017 | P |  17847 | ' assistant'
0018 | P |     13 | '.'
0019 | P | 151645 | '<|im_end|>'
0020 | P |    198 | '\\n'
0021 | P | 151644 | '<|im_start|>'
0022 | P |    872 | 'user'
0023 | P |    198 | '\\n'
0024 | P |  35127 | 'Give'
0025 | P |    752 | ' me'
0026 | P |    264 | ' a'
0027 | P |   2805 | ' short'
0028 | P |   7271 | ' definition'
0029 | P |    315 | ' of'
0030 | P |    264 | ' a'
0031 | P |  29728 | ' neural'
0032 | P |   3922 | ' network'
0033 | P |     13 | '.'
0034 | P | 151645 | '<|im_end|>'
0035 | P |    198 | '\\n'
0036 | P | 151644 | '<|im_start|>'
0037 | P |  77091 | 'assistant'
0038 | P |    198 | '\\n'
0039 | R |     32 | 'A'
0040 | R |  29728 | ' neural'
0041 | R |   3922 | ' network'
0042 | R |    374 | ' is'
0043 | R |    264 | ' a'
0044 | R |    943 | ' type'
0045 | R |    315 | ' of'
0046 | R |   4625 | ' database'
0047 | R |   1483 | ' used'
0048 | R |    311 | ' to'
0049 | R |   3553 | ' store'
0050 | R |   7602 | ' internet'
0051 | R |   6816 | ' pages'
0052 | R |     13 | '.'
0053 | R | 151645 | '<|im_end|>'
0054 | R |    198 | '\\n'
```
