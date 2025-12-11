"""
Script para testar o endpoint GET /events com filtros opcionais.

Cria:
1. Usuário de teste: vitor@aluno.uece.br (senha: 123)
2. Evento onde ele é convidado (proprietário: outro usuário)
3. Evento onde ele é proprietário

Depois use os comandos curl fornecidos para testar.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.models import models
from src.core.security import pegar_senha_hash
from datetime import datetime, date, time, timedelta

def limpar_dados_teste(db: Session):
    """Remove dados de teste anteriores"""
    print("🧹 Limpando dados de teste anteriores...")
    
    # Buscar usuários de teste (por email OU cpf)
    usuarios_teste = db.query(models.Usuario).filter(
        (models.Usuario.email.in_(['vitor@aluno.uece.br', 'professor@uece.br'])) |
        (models.Usuario.cpf.in_(['12345678901', '98765432100']))
    ).all()
    
    for usuario in usuarios_teste:
        # Remover convidados
        db.query(models.Convidado).filter(
            models.Convidado.id_usuario == usuario.id
        ).delete()
        
        # Remover eventos que ele criou
        eventos = db.query(models.Evento).filter(
            models.Evento.email_proprietario == usuario.email
        ).all()
        
        for evento in eventos:
            # Remover ocorrências
            db.query(models.OcorrenciaEvento).filter(
                models.OcorrenciaEvento.id_evento == evento.id
            ).delete()
            
            # Remover convidados do evento
            db.query(models.Convidado).filter(
                models.Convidado.id_evento == evento.id
            ).delete()
            
            # Remover disciplina (se existir)
            db.query(models.DisciplinaDias).filter(
                models.DisciplinaDias.id_disciplina == evento.id
            ).delete()
            
            db.query(models.CursoDisciplina).filter(
                models.CursoDisciplina.id_disciplina == evento.id
            ).delete()
            
            db.query(models.Disciplina).filter(
                models.Disciplina.id_evento == evento.id
            ).delete()
            
            # Remover evento
            db.delete(evento)
        
        # Remover Aluno (se for aluno)
        db.query(models.Aluno).filter(
            models.Aluno.id_usuario == usuario.id
        ).delete()
        
        # Remover Professor (se for professor)
        db.query(models.Professor).filter(
            models.Professor.id_usuario == usuario.id
        ).delete()
        
        # Remover usuário
        db.delete(usuario)
    
    db.commit()
    print("✅ Dados de teste limpos\n")


def criar_usuario_teste(db: Session):
    """Cria usuário de teste: vitor@aluno.uece.br"""
    print("👤 Criando usuário de teste...")
    
    # Buscar ou criar universidade UECE
    uece = db.query(models.Universidade).filter(
        models.Universidade.sigla == "UECE"
    ).first()
    
    if not uece:
        uece = models.Universidade(
            nome="Universidade Estadual do Ceará",
            sigla="UECE",
            cnpj="07885809000127",
            email="contato@uece.br",
            senha=pegar_senha_hash("admin123")
        )
        db.add(uece)
        db.flush()
    
    # Buscar ou criar curso
    curso = db.query(models.Curso).filter(
        models.Curso.sigla == "CC"
    ).first()
    
    if not curso:
        curso = models.Curso(
            nome="Ciência da Computação",
            sigla="CC",
            email="cc@aluno.uece.br",
            id_universidade=uece.id,
            graduacao=True
        )
        db.add(curso)
        db.flush()
    
    # Criar usuário Vitor
    usuario_vitor = models.Usuario(
        nome="Vitor Teste",
        email="vitor@aluno.uece.br",
        cpf="12345678901",
        senha=pegar_senha_hash("123")
    )
    db.add(usuario_vitor)
    db.flush()
    
    # Criar registro de aluno
    aluno = models.Aluno(
        id_usuario=usuario_vitor.id,
        id_curso=curso.id,
        matricula="1234567"
    )
    db.add(aluno)
    
    # Criar usuário professor (proprietário de evento)
    usuario_prof = models.Usuario(
        nome="Professor Teste",
        email="professor@uece.br",
        cpf="98765432100",
        senha=pegar_senha_hash("123")
    )
    db.add(usuario_prof)
    db.flush()
    
    # Criar registro de professor
    professor = models.Professor(
        id_usuario=usuario_prof.id,
        id_universidade=uece.id
    )
    db.add(professor)
    
    db.commit()
    print(f"✅ Usuários criados:")
    print(f"   - {usuario_vitor.email} (ID: {usuario_vitor.id})")
    print(f"   - {usuario_prof.email} (ID: {usuario_prof.id})\n")
    
    return usuario_vitor, usuario_prof, uece


def criar_evento_convidado(db: Session, usuario_vitor, usuario_prof, uece):
    """Cria evento onde Vitor é convidado (proprietário: professor)"""
    print("📅 Criando Evento 1 - Vitor como CONVIDADO...")
    
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    amanha = hoje + timedelta(days=1)
    daqui_7_dias = hoje + timedelta(days=7)
    
    evento1 = models.Evento(
        nome="Aula de Python",
        descricao="Introdução ao Python",
        id_universidade=uece.id,
        data_inicio=amanha,
        data_termino=daqui_7_dias,
        horario_inicio=time(14, 0),
        horario_termino=time(16, 0),
        local_padrao="Lab 01",
        recorrencia="diario_uteis",
        categoria="Aula",
        email_proprietario=usuario_prof.email
    )
    db.add(evento1)
    db.flush()
    
    # Gerar ocorrências (dias úteis)
    data_atual = amanha
    while data_atual <= daqui_7_dias:
        if data_atual.weekday() < 5:  # Segunda a Sexta
            ocorrencia = models.OcorrenciaEvento(
                id_evento=evento1.id,
                data=data_atual,
                local="Lab 01",
                horario_inicio=time(14, 0),
                horario_termino=time(16, 0)
            )
            db.add(ocorrencia)
        data_atual += timedelta(days=1)
    
    # Convidar Vitor
    convidado = models.Convidado(
        id_evento=evento1.id,
        id_usuario=usuario_vitor.id
    )
    db.add(convidado)
    
    db.commit()
    print(f"✅ Evento '{evento1.nome}' criado (ID: {evento1.id})")
    print(f"   - Proprietário: {usuario_prof.email}")
    print(f"   - Convidado: {usuario_vitor.email}")
    print(f"   - Categoria: {evento1.categoria}")
    print(f"   - Período: {amanha.date()} até {daqui_7_dias.date()}\n")
    
    return evento1


def criar_evento_proprietario(db: Session, usuario_vitor, uece):
    """Cria evento onde Vitor é proprietário"""
    print("📅 Criando Evento 2 - Vitor como PROPRIETÁRIO...")
    
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    daqui_2_dias = hoje + timedelta(days=2)
    daqui_5_dias = hoje + timedelta(days=5)
    
    evento2 = models.Evento(
        nome="Reunião de Projeto",
        descricao="Discussão do TCC",
        id_universidade=uece.id,
        data_inicio=daqui_2_dias,
        data_termino=daqui_5_dias,
        horario_inicio=time(10, 0),
        horario_termino=time(11, 0),
        local_padrao="Sala 302",
        recorrencia="diario",
        categoria="Reuniao",
        email_proprietario=usuario_vitor.email
    )
    db.add(evento2)
    db.flush()
    
    # Gerar ocorrências (todos os dias)
    data_atual = daqui_2_dias
    while data_atual <= daqui_5_dias:
        ocorrencia = models.OcorrenciaEvento(
            id_evento=evento2.id,
            data=data_atual,
            local="Sala 302",
            horario_inicio=time(10, 0),
            horario_termino=time(11, 0)
        )
        db.add(ocorrencia)
        data_atual += timedelta(days=1)
    
    # Vitor se adiciona automaticamente como convidado do próprio evento
    convidado = models.Convidado(
        id_evento=evento2.id,
        id_usuario=usuario_vitor.id
    )
    db.add(convidado)
    
    db.commit()
    print(f"✅ Evento '{evento2.nome}' criado (ID: {evento2.id})")
    print(f"   - Proprietário: {usuario_vitor.email}")
    print(f"   - Categoria: {evento2.categoria}")
    print(f"   - Período: {daqui_2_dias.date()} até {daqui_5_dias.date()}\n")
    
    return evento2


def mostrar_comandos_curl(evento1, evento2):
    """Mostra comandos curl para testar"""
    hoje = date.today()
    amanha = hoje + timedelta(days=1)
    
    print("=" * 70)
    print("🧪 COMANDOS PARA TESTAR COM CURL")
    print("=" * 70)
    
    print("\n1️⃣  LOGIN (obter token):")
    print("-" * 70)
    print('curl -X POST "http://localhost:8000/api/auth/login" \\\n+  -H "Content-Type: application/json" \\\n+  -d "{\'email\':\'vitor@aluno.uece.br\',\'password\':\'123\'}"')
    print("\n📝 Copie o 'access_token' da resposta e use nas próximas requisições\n")

    print("2️⃣  LISTAR TODAS OCORRÊNCIAS do usuário:")
    print("-" * 70)
    print('curl -X GET "http://localhost:8000/api/events/" \\\n+  -H "Authorization: Bearer SEU_TOKEN_AQUI"')
    print(f"\n   Deve retornar ~9 ocorrências (2 eventos combinados)\n")

    print("3️⃣  FILTRAR por DATA (amanhã):")
    print("-" * 70)
    print(f'curl -X GET "http://localhost:8000/api/events/?data={amanha}" \\\n+  -H "Authorization: Bearer SEU_TOKEN_AQUI"')
    print(f"\n   Deve retornar apenas ocorrências de {amanha}\n")

    print("4️⃣  FILTRAR por CATEGORIA (Aula):")
    print("-" * 70)
    print('curl -X GET "http://localhost:8000/api/events/?categoria=Aula" \\\n+  -H "Authorization: Bearer SEU_TOKEN_AQUI"')
    print(f"\n   Deve retornar apenas o evento '{evento1.nome}'\n")

    print("5️⃣  FILTRAR por CATEGORIA (Reuniao):")
    print("-" * 70)
    print('curl -X GET "http://localhost:8000/api/events/?categoria=Reuniao" \\\n+  -H "Authorization: Bearer SEU_TOKEN_AQUI"')
    print(f"\n   Deve retornar apenas o evento '{evento2.nome}'\n")

    print("6️⃣  FILTRAR por DATA + CATEGORIA:")
    print("-" * 70)
    print(f'curl -X GET "http://localhost:8000/api/events/?data={amanha}&categoria=Aula" \\\n+  -H "Authorization: Bearer SEU_TOKEN_AQUI"')
    print(f"\n   Deve retornar apenas '{evento1.nome}' em {amanha}\n")
    
    print("=" * 70)
    print("✅ Dados criados! Execute os comandos acima para testar.")
    print("=" * 70)


def main():
    print("\n" + "=" * 70)
    print("🚀 SCRIPT DE TESTE - GET /events com filtros")
    print("=" * 70 + "\n")
    
    db = SessionLocal()
    
    try:
        # Limpar dados anteriores
        limpar_dados_teste(db)
        
        # Criar usuários
        usuario_vitor, usuario_prof, uece = criar_usuario_teste(db)
        
        # Criar eventos
        evento1 = criar_evento_convidado(db, usuario_vitor, usuario_prof, uece)
        evento2 = criar_evento_proprietario(db, usuario_vitor, uece)
        
        # Mostrar comandos curl
        mostrar_comandos_curl(evento1, evento2)
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
