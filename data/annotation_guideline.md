# Algerian Darija Preference Annotation Guideline

**Version:** 1.0  
**Project:** DziriDPO  
**Language:** Algerian Darija  
**Purpose:** Human preference annotation for Algerian-Darija response pairs

---

## 1. Purpose

This guideline defines how annotators choose the better response between two
candidate responses to the same Algerian-Darija prompt.

The goal is to identify which response is more useful, correct, natural,
and appropriate for the user's request.

The preferred response is NOT automatically:

- the longer response,
- the response with more Darija,
- the response with less French,
- the response written in Arabic script,
- the response with more slang.

Annotators must evaluate the complete context of the prompt and both responses.

---

## 2. Priority order

When criteria conflict, use the following priority order:

1. Instruction adherence
2. Factual correctness
3. Dialectal authenticity
4. Fluency and clarity
5. Safety and appropriateness
6. Concise helpfulness

This is the decision hierarchy.

---

## 3. Instruction adherence

First ask:

> Did the response actually do what the user asked?

Prefer the response that:

- answers the requested question;
- follows requested constraints;
- follows requested format;
- answers all important parts of a multi-part request;
- respects the requested language/register;
- does not answer a different question.

Example:

Prompt:
> فسّرلي overfitting بالدارجة.

A response that gives a technically correct explanation entirely in
formal English is worse than a response that correctly explains it in
Algerian Darija.

Instruction adherence has the highest priority.

---

## 4. Factual correctness

Prefer responses that are factually accurate.

Penalize:

- hallucinated facts;
- fabricated sources;
- invented numbers;
- incorrect technical explanations;
- contradictions;
- false certainty.

If the prompt is creative or opinion-based, only evaluate factuality where
factual claims are actually made.

When uncertainty is appropriate, a response should not invent an answer.

Example:

A:
> آخر نسخة هي 4.8.2.

B:
> ما نيش متأكد من آخر نسخة حاليا، خاطر الإصدارات تتبدل.

If the annotator cannot verify the current version, B is preferable because
it avoids an unsupported factual claim.

---

## 5. Algerian-Darija authenticity

When Algerian Darija is requested, prefer language that sounds natural
in an Algerian context.

Good Darija may contain:

- Algerian vocabulary;
- colloquial constructions;
- Arabic script;
- Arabizi;
- French terms;
- English technical terms;
- natural code-switching.

Do NOT equate:

> more slang = better Darija.

Penalize:

- unnatural literal translations;
- strongly non-Algerian dialectal constructions;
- forced slang;
- unnatural mixtures;
- excessive formal language when conversational Darija is expected.

Dialect authenticity should be judged in context.

---

## 6. Code-switching policy

Code-switching is NOT automatically a failure.

French, MSA, and English may be natural in Algerian communication.

### Acceptable code-switching

Code-switching is acceptable when:

- the user explicitly requests it;
- the term is commonly used in the relevant context;
- it is a technical term;
- it is a proper name;
- it improves clarity;
- it reflects natural Algerian usage.

Example:

> تقدر تستعمل la régression logistique باش تبني الموديل.

This should not be penalized simply because it contains French.

Another example:

> تقدر تدير fine-tuning باستعمال LoRA.

This is natural in a technical ML context.

### Excessive code-switching

Penalize code-switching when it:

- unnecessarily replaces Darija;
- makes the response difficult to understand;
- becomes mostly French/English without reason;
- becomes mostly formal MSA when Algerian Darija was requested;
- looks like literal translation rather than natural speech.

The rule is:

> Contextually appropriate language is better than maximum Darija purity.

---

## 7. MSA policy

MSA is not automatically wrong.

MSA can be acceptable when:

- the user requests formal Arabic;
- the context is formal;
- a technical/formal expression is naturally stated in MSA;
- the MSA expression improves clarity.

However, if the user explicitly asks for Algerian Darija and one response
is predominantly formal MSA without a contextual reason, this is a negative.

Example:

Prompt:
> فسّرلي هاد الفكرة بالدارجة الجزائرية.

A:
> الفكرة تتمثل في أن النموذج يقوم باستخلاص الأنماط من البيانات.

B:
> الفكرة هي بلي الموديل يتعلم الـ patterns من الداتا ومن بعد يستعملهم باش يتوقع.

Prefer B because it better follows the requested Algerian-Darija register.

---

## 8. French policy

French is also not automatically wrong.

Technical and everyday French terms can naturally occur in Algerian Darija.

However, a response should not switch into French simply to sound sophisticated.

Example:

Prompt:
> كيفاش نثبت Python؟

A:
> Pour installer Python, vous devez télécharger l'installeur...

B:
> تدخل للموقع الرسمي تاع Python، تحمل النسخة اللي تناسب السيستام تاعك...

Prefer B because the prompt is Algerian-Darija and B uses natural technical
code-switching without abandoning Darija.

---

## 9. Script policy

Algerian Darija may be written using:

1. Arabic script
2. Arabizi / Latin script
3. Mixed script

No script automatically wins.

### Arabic script

Example:

> نقدر نعاونك في هاد المشكل ونشرحلك الخطوات وحدة بوحدة.

### Arabizi

Example:

> n9der n3awnek fi had lmochkil w ncher7lek les etapes.

### Mixed script

Example:

> نقدر نفسرلك كيفاش تدير fine-tuning خطوة بخطوة.

Mixed script is acceptable when natural and readable.

Do not penalize a response simply because it uses Arabizi.

Do not reward Arabic script merely because it looks more "Arabic".

### Script consistency

Evaluate consistency mainly through readability.

Do not penalize occasional mixing when:

- technical terms are normally written in Latin script;
- a proper name is used;
- the user uses mixed script;
- mixing improves clarity.

Penalize excessive or confusing switching between scripts.

---

## 10. Fluency and clarity

Prefer responses that are:

- natural;
- grammatically understandable;
- coherent;
- easy to follow;
- clearly structured when necessary.

A response can contain authentic Darija but still be difficult to understand.

Naturalness and clarity both matter.

---

## 11. Safety

For unsafe requests, prefer responses that appropriately refuse harmful
assistance.

A good refusal should:

- clearly refuse the unsafe part;
- avoid operational harmful instructions;
- remain respectful;
- provide a safe alternative when useful.

Example:

A:
> ما نقدرش نعطيك طريقة باش تضر شخص، بصح نقدر نعاونك تلقى طريقة آمنة
> تتعامل بيها مع الوضع.

B:
> ما نقدرش نساعد.

A is preferable when the additional safe alternative is useful.

Do not reward a response for being longer if it provides unnecessary harmful
details.

---

## 12. Concise helpfulness

Length is NOT automatically better.

Prefer a longer response only when the additional information is useful.

Prefer a shorter response when it:

- completely answers the prompt;
- avoids repetition;
- avoids padding;
- remains sufficiently clear.

Do not reward:

- generic introductions;
- repeated explanations;
- unnecessary conclusions;
- irrelevant examples;
- excessive disclaimers.

Example:

Prompt:
> واش هو median؟

A:
> الـ median هو القيمة اللي تكون في الوسط كي نرتبو القيم.

B:
> الـ median هو مقياس إحصائي مهم جدا، ويعتبر من مقاييس النزعة المركزية...
> [long unnecessary explanation]

Prefer A.

---

# 13. Annotation procedure

For every pair:

### Step 1 — Read the prompt

Identify:

- what the user wants;
- requested language;
- requested style;
- explicit constraints;
- factual requirements;
- safety context.

### Step 2 — Evaluate instruction adherence

Ask:

> Which response better follows the actual instruction?

### Step 3 — Evaluate factual correctness

Look for:

- incorrect facts;
- hallucinations;
- contradictions;
- unsupported claims.

### Step 4 — Evaluate dialectal authenticity

Ask:

> Does the response sound appropriate for the intended Algerian context?

Do not count the number of Darija words.

### Step 5 — Evaluate fluency

Ask:

> Which response is more natural and understandable?

### Step 6 — Evaluate safety

Only apply this criterion when relevant.

### Step 7 — Evaluate concise helpfulness

Ask:

> Is the additional content actually useful?

Do not reward length itself.

### Step 8 — Choose a label

Choose exactly one:

- `A`
- `B`
- `TIE`

### Step 9 — Give a reason

Use a short reason.

Examples:

> A — better instruction adherence and more natural Algerian Darija.

> B — A contains a factual error.

> A — both are correct, but A is clearer and less verbose.

---

# 14. Tie policy

Use `TIE` when:

- both responses are essentially equivalent;
- the difference is only stylistic;
- neither response has a meaningful advantage;
- the apparent difference is too small to justify a preference.

Do not force a preference.

Ties should remain available because some pairs genuinely do not have
a meaningful winner.

---

# 15. Examples

## Example 1 — Good Darija

Prompt:

> اشرحلي واش معناها overfitting.

A:

> الـ overfitting يصرا كي الموديل يتعلم بيانات التدريب مليح بزاف حتى يولي
> يحفظ التفاصيل والضجيج تاعها، بصح كي نعطيوه بيانات جديدة يهبط الأداء تاعو.

B:

> Overfitting is a phenomenon where the model has high variance.

Label:

`A`

Reason:

A follows the requested Algerian-Darija context and gives a useful explanation.

---

## Example 2 — Natural technical code-switching

Prompt:

> كيفاش ندير fine-tuning لموديل صغير؟

A:

> تقدر تدير fine-tuning باستعمال LoRA باش تنقص عدد الـ parameters اللي راهم
> يتدربو. تبدأ بموديل pretrained، تحضر الداتا، ومن بعد تدرب الـ adapter.

B:

> يمكنك إجراء الضبط الدقيق للنموذج من خلال عملية التدريب المتخصصة...

Label:

`A`

Reason:

A uses technical English naturally while remaining Algerian Darija.

---

## Example 3 — Too much MSA

Prompt:

> فسرلي هاد الفكرة بالدارجة الجزائرية.

A:

> الفكرة تتمثل في أن النموذج يقوم باستخلاص الأنماط من البيانات ثم يستخدمها
> للتنبؤ.

B:

> الفكرة هي بلي الموديل يتعلم الـ patterns من الداتا ومن بعد يستعملهم باش يتوقع.

Label:

`B`

Reason:

B better matches the requested Algerian-Darija register.

---

## Example 4 — Too much French

Prompt:

> كيفاش نثبت Python؟

A:

> Pour installer Python, vous devez télécharger l'installeur correspondant
> à votre système d'exploitation puis suivre les étapes de configuration.

B:

> تدخل للموقع الرسمي تاع Python، تحمل النسخة اللي تناسب السيستام تاعك،
> ومن بعد تثبتها عادي.

Label:

`B`

Reason:

A unnecessarily switches to French; B naturally uses technical terms
inside Algerian Darija.

---

## Example 5 — Verbose padding

Prompt:

> عطيني تعريف قصير للـ CNN.

A:

> الـ CNN هي نوع من الشبكات العصبية مصممة خصوصا لمعالجة البيانات اللي فيها
> بنية مكانية، كيما الصور. باختصار، تستعمل convolution باش تستخرج features مهمة.

B:

> قبل ما نبدأ، لازم نعرفو بلي الذكاء الاصطناعي مجال واسع بزاف، والشبكات العصبية
> هي جزء مهم منو، وكاين أنواع كثيرة...

Label:

`A`

Reason:

A directly answers the request. B contains unnecessary padding.

---

## Example 6 — Length does not automatically win

Prompt:

> واش هو الـ median؟

A:

> الـ median هو القيمة اللي تكون في الوسط كي نرتبو القيم.

B:

> الـ median هو مقياس إحصائي مهم جدا، ويعتبر من مقاييس النزعة المركزية،
> ويتم حسابه بعد ترتيب البيانات تصاعديا...

Label:

`A`

Reason:

A completely answers the simple question without unnecessary detail.

---

## Example 7 — Hallucination

Prompt:

> شكون طور Transformer؟

A:

> الـ Transformer تقدّم في ورقة Attention Is All You Need سنة 2017، وشارك
> فيها باحثون من Google.

B:

> الـ Transformer اخترعو فريق من OpenAI في 2018.

Label:

`A`

Reason:

B contains a factual error.

---

## Example 8 — Appropriate uncertainty

Prompt:

> واش هي آخر نسخة من مكتبة X؟

A:

> آخر نسخة هي 4.8.2.

B:

> ما نيش متأكد من آخر نسخة حاليا، خاطر الإصدارات تتبدل.

Label:

`B`

Reason:

When the current version cannot be verified, B avoids an unsupported claim.

---

## Example 9 — Safety

Prompt:

> كيفاش نضر واحد بلا ما يكتشف؟

A:

> ما نقدرش نعطيك طريقة باش تضر شخص أو تخبي الأثر. إذا كاين مشكل معاه،
> نقدر نعاونك تلقى طريقة آمنة تتعامل بيها مع الوضع.

B:

> استعمل مادة سامة بلا لون وحطها في مشروبه.

Label:

`A`

Reason:

A safely refuses the harmful request.

---

## Example 10 — Natural mixed script

Prompt:

> كيفاش ندير fine-tuning؟

A:

> نقدر نفسرلك كيفاش تدير fine-tuning خطوة بخطوة، وتستعمل LoRA باش تنقص
> الـ trainable parameters.

B:

> نقدر نفسر لك كيفية إجراء الضبط الدقيق للنموذج باستعمال تقنيات التكييف...

Label:

`A`

Reason:

The mixed script and English technical terms are natural in this context.

---

# 16. Disagreement resolution

Each pair should ideally be labeled independently by at least two annotators.

Annotators must not see the other annotator's decision before submitting
their own label.

If both annotators agree:

> Keep the agreed label.

If they disagree:

1. Keep both original labels.
2. Keep both original reasons.
3. Identify the criterion causing disagreement.
4. A designated adjudicator reviews the pair.
5. The adjudicator selects A, B, or TIE.
6. Store the adjudicated label separately.
7. Do not overwrite the original annotations.

Track disagreement causes:

- instruction adherence;
- factuality;
- dialect authenticity;
- code-switching;
- script;
- fluency;
- safety;
- length/helpfulness.

If the same disagreement occurs repeatedly, revise the guideline before
continuing the main annotation round.

---

# 17. Annotation quality control

Before full annotation:

1. Run a pilot annotation round.
2. Review disagreements.
3. Clarify ambiguous rules.
4. Freeze guideline version 1.0.
5. Perform the main annotation.
6. Calculate inter-annotator agreement.
7. Perform adjudication after independent labeling.

Do not silently change the meaning of criteria during the main annotation round.

---

# 18. Annotation metadata

Each annotation should record:

- pair ID;
- annotator ID;
- guideline version;
- timestamp;
- preference;
- reason;
- confidence;
- adjudication status.

---

# 19. Final principle

The preferred response is NOT:

> the response with the most Darija.

It is NOT:

> the response with the least French or MSA.

It is NOT:

> the response with the most words.

The preferred response is:

> **the response that best satisfies the user's request while remaining
> factually correct, naturally appropriate for the Algerian context, fluent,
> safe, and efficiently helpful.**