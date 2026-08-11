# Preference Data Audit

## Dataset summary

- Input examples: 3
- Valid examples: 3
- Rejected examples: 0

## Filtering rules

An example is rejected when:

- required fields are missing
- fields have invalid types
- the prompt is empty
- the chosen response is empty
- the rejected response is empty
- chosen and rejected responses are identical
- the example ID is duplicated

Invalid examples are not silently discarded; rejection reasons are recorded.

## Rejection reasons

- None

## Length statistics

- Number of valid examples: 3
- Mean chosen length: 44.67 characters
- Median chosen length: 31.00 characters
- Mean rejected length: 38.33 characters
- Median rejected length: 32.00 characters
- Mean length ratio: 1.11
- Median length ratio: 1.03

## Manual inspection sample

The following examples were sampled with seed `42`.

### Example 1 — `tiny_001`

**Prompt**

> What is 2 + 2?

**Chosen**

> 2 + 2 equals 4.

**Rejected**

> 2 + 2 equals 5.

**Manual decision:** TODO

### Example 2 — `tiny_002`

**Prompt**

> What is the capital of France?

**Chosen**

> The capital of France is Paris.

**Rejected**

> The capital of France is Berlin.

**Manual decision:** TODO

### Example 3 — `tiny_003`

**Prompt**

> Give me a short definition of a neural network.

**Chosen**

> A neural network is a model made of interconnected layers that learn patterns from data.

**Rejected**

> A neural network is a type of database used to store internet pages.

**Manual decision:** TODO

## Filtering decision

TODO: record the final decision after manual inspection.
1. Do chosen and rejected answer the SAME prompt?
2. Is chosen genuinely better?
3. Is rejected genuinely worse?
4. Is either response obviously malformed?
5. Is the preference mainly explained by length?