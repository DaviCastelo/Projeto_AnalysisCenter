from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from fpdf import FPDF
import mysql.connector
from mysql.connector import Error
import os

app = Flask(__name__)
app.secret_key = '1234'  # Substitua com uma chave secreta adequada

# Função para conectar ao banco de dados MySQL
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='analysiscenter',
            user='root',  # Substitua com seu usuário MySQL
            password='Filhotes3'  # Substitua com sua senha MySQL
        )
        if connection.is_connected():
            print('Conexão ao MySQL bem-sucedida.')
            return connection
    except Error as e:
        print(f'Erro ao conectar ao MySQL: {e}')
        return None

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para a página Black List
@app.route('/blacklist', methods=['GET', 'POST'])
def blacklist():
    if request.method == 'POST':
        cpf = request.form['cpf']
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor(dictionary=True)
            try:
                query = "SELECT * FROM black_list WHERE cpf = %s"
                cursor.execute(query, (cpf,))
                result = cursor.fetchone()
                cursor.fetchall()  # Certifique-se de que todos os resultados sejam lidos
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

# Rota para adicionar um CPF à Black List
@app.route('/add_blacklist', methods=['POST'])
def add_blacklist():
    nome = request.form['nome']
    cpf = request.form['cpf']
    motivo = request.form['motivo']
    
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

# Rota para excluir um CPF da Black List
@app.route('/delete_blacklist', methods=['POST'])
def delete_blacklist():
    cpf = request.form['cpf']
    
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

# Função para dividir texto longo em múltiplas linhas
def wrap_text(text, max_width, pdf):
    lines = []
    words = text.split()
    current_line = ""
    for word in words:
        if pdf.get_string_width(current_line + word + " ") <= max_width:
            current_line += word + " "
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)
    return lines

# Rota para gerar PDF
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    nome = request.form['nome']
    cpf = request.form['cpf']
    motivo = request.form['motivo']

    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Resultado da consulta na Black List', 0, 1, 'C')
    
    # Adicionar "NEGATIVADO" centralizado e em vermelho
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(255, 0, 0)  # Define a cor do texto para vermelho (RGB)
    pdf.cell(0, 10, 'NEGATIVADO', 0, 1, 'C')
    
    # Resetar a cor do texto para preto
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Nome: {nome}', 0, 1)
    pdf.cell(0, 10, f'CPF: {cpf}', 0, 1)
    
    # Dividir o texto do motivo em múltiplas linhas
    max_width = 190  # Largura máxima da célula em mm
    lines = wrap_text(motivo, max_width, pdf)
    pdf.cell(0, 10, 'Motivo:', 0, 1)
    for line in lines:
        pdf.cell(0, 10, line, 0, 1)
    
    # Adicionar espaçamento antes da imagem
    pdf.ln(10)  # Adicionar espaçamento após o texto
    
    # Atualizar caminho da imagem e reduzir o tamanho pela metade
    image_path = 'fotos/Imagem do WhatsApp de 2024-06-18 à(s) 22.26.19_d93155f5.jpg'
    image_width = 50  # Largura da imagem em mm
    pdf_width = pdf.w - 2 * pdf.l_margin  # Largura da página menos margens
    x = (pdf_width - image_width) / 2 + 5  # Posição x ajustada para centralizar a imagem com pequeno deslocamento à direita
    y = pdf.get_y()  # Posição y atual para garantir que a imagem fique abaixo do texto
    
    # Adicionar a imagem
    pdf.image(image_path, x=x, y=y, w=image_width)
    
    output_filename = f"{nome}_blacklist.pdf"
    pdf.output(output_filename)

    return send_file(output_filename, as_attachment=True, download_name=output_filename)

if __name__ == '__main__':
    app.run(debug=True)
