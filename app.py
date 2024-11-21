from flask import Flask, json, make_response, render_template, request, redirect, url_for, flash, session, send_file
from fpdf import FPDF
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import os
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = '1234'  

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='analysiscenter',
            user='root',
            password='gn020603'
            # password='nova_senha'
        )
        if connection.is_connected():
            print('Conexão ao MySQL bem-sucedida.')
            return connection
    except Error as e: 
        print(f'Erro ao conectar ao MySQL: {e}')
        return None

# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'user_id' not in session:
#             flash('Você precisa estar logado para acessar esta página.')
#             return redirect(url_for('login'))
#         return f(*args, **kwargs)
#     return decorated_function

@app.route('/')
def home():
    # if 'user_id' not in session:
    #     return redirect(url_for('login'))
    return redirect(url_for('index'))

@app.route('/index')
# @login_required
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        cpf = request.form.get('cpf', '')
        cnpj = request.form.get('cnpj', '')
        endereco = request.form.get('endereco', '')
        telefone = request.form.get('telefone', '')
        empresa = request.form.get('empresa', '')
        atividade = request.form.get('atividade', '')
        senha = request.form.get('senha', '')
        nome = request.form.get('nome', '')
        email = request.form.get('email', '')  
        
        # Ajuste para plano_id: atribuir None se estiver vazio
        plano_id = request.form.get('plano') or None  

        hashed_password = generate_password_hash(senha)

        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            query = """
                INSERT INTO users (cpf, cnpj, endereco, telefone, empresa, atividade, senha, nome, email, plano_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            try:
                cursor.execute(query, (cpf, cnpj, endereco, telefone, empresa, atividade, hashed_password, nome, email, plano_id))
                connection.commit()
                flash('Registro realizado com sucesso! Faça o login.')
                return redirect(url_for('login'))
            except mysql.connector.IntegrityError:
                flash('CPF ou CNPJ já cadastrado. Tente outro.')
                return redirect(url_for('register'))
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Erro ao conectar ao banco de dados.')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form.get('cpf', '')
        senha = request.form.get('senha', '')

        if not cpf:
            flash('O CPF deve ser preenchido.')
            return redirect(url_for('login'))

        connection = connect_to_database()
        if connection:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE cpf = %s"
            cursor.execute(query, (cpf,))
            user = cursor.fetchone()
            cursor.fetchall()  # Ensure all results are fetched or processed
            cursor.close()
            connection.close()

            if user and check_password_hash(user['senha'], senha):
                session['user_id'] = user['id']
                session['email'] = user['email']
                flash('Login realizado com sucesso!')
                return redirect(url_for('index'))
            else:
                flash('CPF ou senha incorretos.')
                return redirect(url_for('login'))
        else:
            flash('Erro ao conectar ao banco de dados.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
# @login_required
def logout():
    session.pop('user_id', None)  # Remove o ID do usuário da sessão
    session.pop('email', None)    # Remove o e-mail da sessão
    flash('Logout realizado com sucesso!')
    return redirect(url_for('login'))  # Redireciona para a página de login


@app.route('/blacklist', methods=['GET', 'POST'])
def blacklist():
    if request.method == 'POST':
        cpf = request.form.get('cpf', '')
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor(dictionary=True)
            try:
                query = "SELECT * FROM black_list WHERE cpf = %s"
                cursor.execute(query, (cpf,))
                result = cursor.fetchone()
                cursor.fetchall()  # Ensure all results are fetched or processed
                if result:
                    negativado = 'NEGATIVADO'
                    return render_template('blacklist.html', resultado=result, negativado=negativado)
                else:
                    return render_template('blacklist.html', mensagem='CPF não encontrado na Black List.')
            finally:
                cursor.close()
                connection.close()
        else:
            return 'Erro ao conectar ao banco de dados'
    else:
        return render_template('blacklist.html')

@app.route('/add_blacklist', methods=['POST'])
# @login_required
def add_blacklist():
    nome = request.form.get('nome', '')
    cpf = request.form.get('cpf', '')
    motivo = request.form.get('motivo', '')
    
    connection = connect_to_database()
    if connection:
        cursor = connection.cursor()
        query = "INSERT INTO black_list (nome, cpf, motivo) VALUES (%s, %s, %s)"
        cursor.execute(query, (nome, cpf, motivo))
        connection.commit()
        cursor.close()
        connection.close()
        
        flash('CPF adicionado à black list com sucesso!')
        return redirect(url_for('blacklist'))
    else:
        return 'Erro ao conectar ao banco de dados'

@app.route('/delete_blacklist', methods=['POST'])
# @login_required
def delete_blacklist():
    cpf = request.form.get('cpf', '')
    
    connection = connect_to_database()
    if connection:
        cursor = connection.cursor()
        query = "DELETE FROM black_list WHERE cpf = %s"
        cursor.execute(query, (cpf,))
        connection.commit()
        cursor.close()
        connection.close()
        
        flash('CPF excluído da black list com sucesso!')
        return redirect(url_for('blacklist'))
    else:
        flash('Erro ao conectar ao banco de dados')
        return redirect(url_for('blacklist'))

@app.route('/add_blacklist_form', methods=['GET'])
def add_blacklist_form():
    return render_template('add_blacklist.html')

@app.route('/delete_blacklist_form', methods=['GET'])
def delete_blacklist_form():
    return render_template('delete_blacklist.html')

@app.route('/edit_blacklist', methods=['POST', 'GET'])
# @login_required
def edit_blacklist():
    if request.method == 'POST':
        cpf = request.form.get('cpf', '')
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM black_list WHERE cpf = %s"
            cursor.execute(query, (cpf,))
            result = cursor.fetchone()
            cursor.fetchall()  # Ensure all results are fetched or processed
            cursor.close()
            connection.close()

            if result:
                return render_template('edit_blacklist.html', result=result)
            else:
                flash('CPF não encontrado na Black List.')
                return redirect(url_for('blacklist'))
        else:
            flash('Erro ao conectar ao banco de dados.')
            return redirect(url_for('blacklist'))
    return redirect(url_for('blacklist'))

@app.route('/update_blacklist', methods=['POST'])
# @login_required
def update_blacklist():
    old_cpf = request.form.get('old_cpf', '')  # CPF antigo para buscar o registro a ser atualizado
    new_cpf = request.form.get('new_cpf', '')  # Novo CPF
    nome = request.form.get('nome', '')
    motivo = request.form.get('motivo', '')

    connection = connect_to_database()
    if connection:
        cursor = connection.cursor()
        # Atualizar o registro no banco de dados
        query = "UPDATE black_list SET nome = %s, cpf = %s, motivo = %s WHERE cpf = %s"
        cursor.execute(query, (nome, new_cpf, motivo, old_cpf))
        connection.commit()
        cursor.close()
        connection.close()

        flash('Informações atualizadas com sucesso!')
        return redirect(url_for('blacklist'))
    else:
        flash('Erro ao conectar ao banco de dados.')
        return redirect(url_for('blacklist'))
    
    
@app.route('/gerar_pdf_consulta', methods=['POST'])
def generate_pdf_cpf():
    try:
        nome = request.form.get('name', '')
        cpf = request.form.get('cpf', '')
        telefone = request.form.get('telefone', '')
        email = request.form.get('email', '')
        rg = request.form.get('rg', '')
        endereco = request.form.get('address', '')
        situacao = request.form.get('situacao', '')
        mandado = request.form.get('mandado', '')

        processos = request.form.getlist('processo[]')
        partes = request.form.getlist('partes[]')

        multas_json = request.form.get('multas', '[]')  
        multas = json.loads(multas_json)

        pdf = FPDF()

        pdf.set_left_margin(0)
        pdf.set_right_margin(0)
        pdf.set_top_margin(0)

        pdf.add_page()

        image_path = os.path.join(os.path.dirname(__file__), 'static', 'fotos', 'logo.png')
        image_width = 30  
        image_height = 30  

        pdf.set_fill_color(0, 5, 125)
        pdf.rect(0, 0, pdf.w, image_height + 5, 'F') 

        pdf.image(image_path, x=5, y=5, w=image_width, h=image_height)

        pdf.set_xy(0, 5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 26)
        pdf.cell(pdf.w, image_height, 'RELATÓRIO', 0, 1, 'C')

        pdf.set_left_margin(6)
        pdf.set_right_margin(6)
        pdf.cell(0, 5, '', 0, 1)
        pdf.set_font('Arial', 'B', 12)
        pdf.ln(5) 
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 10, 
            "A Lei Geral de Proteção de Dados Pessoais - LGPD (Lei n. 13.709, de 2018) dispõe sobre a proteção de dados pessoais das pessoas. Portanto, o conteúdo deverá ser apenas para o seu conhecimento e declara ciência que todas as informações contidas no corpo da consulta são apenas para sua orientação."
        )


        current_datetime = datetime.now().strftime('%d/%m/%Y %H:%M')
        pdf.cell(0, 10, current_datetime, 0, 1, 'R')  

#----------------------------------------DADOS PESSOAIS---------------------------------------

        pdf.set_fill_color(0, 5, 125)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'DADOS PESSOAIS', 0, 1, 'C', 1)
        pdf.cell(0, 10, '', 0, 1)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.set_font('Arial', 'B', 12)  
        pdf.cell(20, 10, 'Nome:', 0, 0)  
        pdf.set_font('Arial', '', 12) 
        pdf.cell(0, 10, nome, 0, 1)

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(20, 10, 'CPF:', 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.cell(35, 10, f'{cpf}', 0, 0)
        pdf.set_font('Arial', 'B', 12)
        if situacao == 'REGULAR':
            pdf.set_text_color(19, 136, 56)
        else:
            pdf.set_text_color(156, 25, 38)
        pdf.cell(0, 10, f'  {situacao}', 0, 1)  

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(20, 10, 'Telefone:', 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, telefone, 0, 1)

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(20, 10, 'Email:', 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, email, 0, 1)

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(20, 10, 'RG:', 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, rg, 0, 1)

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(23, 10, 'Endereço:', 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 10, endereco, 0, 1)
        pdf.cell(0, 10, '', 0, 1)

#----------------------------------------BLACKLIST---------------------------------------

        pdf.set_fill_color(156, 25, 38)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'BLACK LIST', 0, 1, 'C', 1)
        pdf.cell(0, 10, '', 0, 1)
        pdf.set_text_color(19, 136, 56)
        pdf.cell(0, 10, 'CPF NÃO ENCONTRADO NA BLACK LIST', 0, 1, 'C')
        pdf.cell(0, 10, '', 0, 1)

#--------------------------------------MULTAS-----------------------------------------

        pdf.set_fill_color(0, 5, 125)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'PRONTUÁRIO DA CNH', 0, 1, 'C', 1)
        pdf.cell(0, 10, '', 0, 1)
        
        pdf.set_text_color(0, 0, 0)

        if multas:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f'MULTAS: {len(multas)}', 0, 1)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(40, 10, 'Pontos', 1)
            pdf.cell(pdf.w - 50, 10, 'Descrição da Infração', 1) 
            pdf.ln()

            pdf.set_font('Arial', '', 10)
            total_pontos = 0
            for multa in multas:
                pontuacao = multa.get('pontuacao', 0)
                descricao = multa.get('descricao', '')

                total_pontos += int(pontuacao)
                pdf.cell(40, 10, str(pontuacao), 1)
                pdf.cell(pdf.w - 50, 10, descricao, 1) 
                pdf.ln()

            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f'TOTAL DE PONTOS: {total_pontos}', 0, 1)
            pdf.cell(0, 10, '', 0, 1)

        else:
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(19, 136, 56)
            pdf.cell(0, 10, 'NÃO CONSTA MULTAS ATÉ A PRESENTE DATA.', 0, 1, 'C')
            pdf.cell(0, 10, '', 0, 1)

#---------------------------------------MANDADOS DE PRISÃO----------------------------------------

        pdf.set_fill_color(0, 5, 125)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'MANDADOS DE PRISÃO', 0, 1, 'C', 1)
        pdf.cell(0, 10, '', 0, 1)
        pdf.set_text_color(0, 0, 0)
        if mandado == 'NÃO EXISTEM MANDADOS DE PRISAO PARA ESTE CPF.':
            pdf.set_text_color(19, 136, 56)
        else:
            pdf.set_text_color(156, 25, 38)
        pdf.cell(0, 10, f'{mandado}', 0, 1, 'C')
        pdf.cell(0, 10, '', 0, 1)

# ----------------------------------------ANÁLISE JUDICIAL---------------------------------------

        pdf.set_fill_color(0, 5, 125)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'ANÁLISE JUDICIAL', 0, 1, 'C', 1)
        pdf.set_text_color(0, 0, 0)

        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, '', 0, 1)

        count_requerente = 0
        count_requerido = 0

        if processos:
            for processo in processos:
                if processo.strip():
                    try:
                        processo_data = json.loads(processo)
                        partes = processo_data.get("Partes", [])
                        if partes:
                            for parte in partes:
                                parte_nome = parte.get("Nome", "").lower()
                                tipo = parte.get("Tipo", "").lower()
                                nome_principal = nome.lower()

                                if nome_principal in parte_nome:
                                    if "requerente" in tipo:
                                        count_requerente += 1
                                    elif "requerido" in tipo:
                                        count_requerido += 1
                    except Exception as e:
                        print(f"Erro ao processar o processo: {str(e)}")

        pdf.set_font('Arial', 'B', 12)

        pdf.set_fill_color(0, 5, 125) 
        pdf.set_text_color(255, 255, 255)  
        pdf.cell(85, 10, f'Como requerente: {count_requerente}', 0, 0, 'C', True)

        pdf.set_fill_color(255, 255, 255)
        pdf.cell(22, 10, '', 0, 0, '', True) 

        pdf.set_fill_color(156, 25, 38)
        pdf.set_text_color(255, 255, 255)  
        pdf.cell(85, 10, f'Como requerido: {count_requerido}', 0, 1, 'C', True)

        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, '', 0, 1)

        if processos:
            for processo in processos:
                if processo.strip():
                    try:
                        processo_data = json.loads(processo)

                        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                        pdf.cell(0, 10, '', 0, 1)
                        pdf.set_font('Arial', 'B', 12)
                        pdf.cell(50, 10, 'Número do Processo:', 0, 0)
                        pdf.set_font('Arial', '', 12)
                        pdf.cell(0, 10, processo_data.get("Numero", "N/A"), 0, 1)

                        pdf.set_font('Arial', 'B', 12)
                        pdf.cell(15, 10, 'Tipo:', 0, 0)
                        pdf.set_font('Arial', '', 12)
                        pdf.cell(0, 10, processo_data.get("Tipo", "N/A"), 0, 1)

                        pdf.set_font('Arial', 'B', 12)
                        pdf.cell(40, 10, 'Nome do Tribunal:', 0, 0)
                        pdf.set_font('Arial', '', 12)
                        pdf.cell(0, 10, processo_data.get("TribunalNome", "N/A"), 0, 1)

                        pdf.set_font('Arial', 'B', 12)
                        pdf.cell(40, 10, 'Tipo do Tribunal:', 0, 0)
                        pdf.set_font('Arial', '', 12)
                        pdf.cell(0, 10, processo_data.get("TribunalTipo", "N/A"), 0, 1)

                        pdf.set_font('Arial', 'B', 12)
                        pdf.cell(20, 10, 'Assunto:', 0, 0)
                        pdf.set_font('Arial', '', 12)
                        pdf.multi_cell(0, 10, processo_data.get("Assunto", "N/A"))

                        pdf.set_font('Arial', 'B', 12)
                        pdf.cell(20, 10, 'Situação:', 0, 0)
                        pdf.set_font('Arial', '', 12)
                        pdf.cell(0, 10, processo_data.get("Situacao", "N/A"), 0, 1)

                        ultima_atualizacao_str = processo_data.get("UltimaAtualizacaoData", "N/A")
                        if ultima_atualizacao_str != "N/A":
                            try:
                                ultima_atualizacao = datetime.fromisoformat(ultima_atualizacao_str)
                                ultima_atualizacao_formatada = ultima_atualizacao.strftime("%d/%m/%Y")
                            except ValueError:
                                ultima_atualizacao_formatada = "Data inválida"
                        else:
                            ultima_atualizacao_formatada = "N/A"

                        pdf.set_font('Arial', 'B', 12)
                        pdf.cell(60, 10, 'Data da última atualização:', 0, 0)
                        pdf.set_font('Arial', '', 12)
                        pdf.cell(0, 10, ultima_atualizacao_formatada, 0, 1)

                        partes = processo_data.get("Partes", [])
                        pdf.cell(0, 10, 'Partes', 0, 1, 'C')
                        pdf.cell(100, 10, 'Nome', 1)
                        pdf.cell(100, 10, 'Tipo', 1)
                        pdf.ln()

                        if partes:
                            for parte in partes:
                                nome_parte = parte.get("Nome", "N/A")
                                tipo_parte = parte.get("Tipo", "N/A")
                                pdf.set_font('Arial', 'B', 9)
                                pdf.cell(100, 10, nome_parte, 1)
                                pdf.cell(100, 10, tipo_parte, 1)
                                pdf.ln()
                                pdf.set_font('Arial', '', 12)
                        else:
                            pdf.cell(0, 10, 'Nenhuma parte envolvida.', 0, 1)

                        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                        pdf.cell(0, 10, '', 0, 1)

                    except Exception as e:
                        print(f"Erro ao processar o processo: {str(e)}")
        else:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Nenhum processo encontrado para este CPF', 0, 1)

        response = make_response(pdf.output(dest='S').encode('latin-1'))
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={nome}-{cpf}.pdf'

        return response

    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")  
        return {"error": "Ocorreu um erro ao gerar o PDF."}, 500



@app.route('/generate_pdf', methods=['POST'])
# @login_required
def generate_pdf():
    nome = request.form.get('nome', '')
    cpf = request.form.get('cpf', '')
    motivo = request.form.get('motivo', '')

    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Resultado da consulta na Black List', 0, 1, 'C')
    
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(0, 10, 'NEGATIVADO', 0, 1, 'C')
    
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Nome: {nome}', 0, 1)
    pdf.cell(0, 10, f'CPF: {cpf}', 0, 1)
    
    pdf.multi_cell(0, 10, f'Motivo: {motivo}', 0, 1)
    
    pdf.ln(10)

    image_path = 'fotos/Imagem_do_WhatsApp_de_2024-06-18_a_s_22.26.19_d93155f5.jpg'
    
    if os.path.exists(image_path):
        pdf_width = pdf.w - 2 * pdf.l_margin
        image_width = 50
        x = (pdf_width - image_width) / 2 + pdf.l_margin
        y = pdf.get_y()
        pdf.image(image_path, x=x, y=y, w=image_width)
    
    output_filename = f"{nome}_blacklist.pdf"
    pdf.output(output_filename)

    return send_file(output_filename, as_attachment=True, download_name=output_filename)


if __name__ == '__main__':
    app.run(debug=True)