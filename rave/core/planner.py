from ..contracts import AgentTask, new_id

SPECIALTIES = [
    ("Fundamentos e evidências", "O que sabemos sobre o objeto, seus componentes e quais evidências sustentam esse conhecimento?", "Mapa factual e conceitual com afirmações e referências."),
    ("Mecanismos, relações e explicações", "Como os elementos funcionam, interagem e produzem os resultados observados?", "Mapa de mecanismos, relações e explicações."),
    ("Perspectivas, limites e complementos", "O que falta considerar, em quais condições a explicação muda e quais limites importam?", "Mapa de condições, exceções, limitações e perspectivas complementares.")]

def create_tasks(run_id: str, question: str, scope: str) -> list[AgentTask]:
    return [AgentTask(new_id("task"), run_id, question, prompt, role, expected, scope,
        ["Não inventar fontes ou evidências.", "Preservar incertezas e limitações.", "Manter foco na especialização atribuída."])
        for role, prompt, expected in SPECIALTIES]
