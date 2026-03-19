set @codnotafiscal = (select pceentradas.codnotafiscal from pceentradas where pceentradas.codpceentradas = @codpceentrada limit 1);
set @existeEntrada = (select pceentradas.codpceentradas from pceentradas where pceentradas.codpceentradas = @codpceentrada limit 1);
set @status_entrada = (select pceentradas.status from pceentradas where pceentradas.codpceentradas = @codpceentrada limit 1);

set @is_fechada = if(@status_entrada = 'True', 1, 0);
set @is_aberta  = if(@status_entrada = 'False', 1, 0);

set @temfinbaixado = ifnull((select if(INSTR(group_concat(if(creddebi.codbaixa = 0, 'False','True')),'True') > 0,'True','False') from creddebi where creddebi.chavecodigo = @codpceentrada and creddebi.chavereferencia = 'pceentradas' and creddebi.chavereferenciaqual = 'PCEEntrada'), 'False');
                              
set @temsaida = ifnull((select if(instr(group_concat(if(pceentradasitensdetalhessaidas.sa_codigo >0,'True','False')),'True') > 0,'True','False') from pceentradasitensdetalhessaidas left join pceentradas on pceentradas.codpceentradas = pceentradasitensdetalhessaidas.codpceentradas where pceentradasitensdetalhessaidas.codpceentradas = @codpceentrada and pceentradas.gerasaida = 'True'), 'False');

set @codsaida = (select pceentradasitensdetalhessaidas.sa_codigo from pceentradasitensdetalhessaidas left join pceentradas on pceentradas.codpceentradas = pceentradasitensdetalhessaidas.codpceentradas where pceentradasitensdetalhessaidas.codpceentradas = @codpceentrada and pceentradas.gerasaida = 'True' and pceentradasitensdetalhessaidas.sa_codigo <> 0 group by pceentradasitensdetalhessaidas.codpceentradas);

set @pode_excluir = if(
    @is_aberta = 1 OR 
    (@is_fechada = 1 AND 
    (@temfinbaixado = 'False' or (@temfinbaixado = 'True' and @confirmacomfinanceiro = 'True')) AND 
    (@temsaida = 'False' or (@temsaida = 'True' and @confirmacomsaida = 'True'))), 
1, 0);

delete from movimentocorrente 
where movimentocorrente.codcreddebi in(select creddebi.codcreddebi from creddebi where chavecodigo = @codpceentrada and chavereferencia = 'pceentradas' and chavereferenciaqual = 'PCEEntrada')
and @is_fechada = 1 and @pode_excluir = 1;

insert into logsistema(nomeusuario,datahora,descricao)
select funcionarios.fu_login, now(), concat('Excluiu Financeiro por Exclusao de Entrada de Material: ',creddebi.codcreddebi) as descricao
from creddebi left join funcionarios on funcionarios.fu_codigo = @codfuncionario
where creddebi.chavecodigo = @codpceentrada and creddebi.chavereferencia = 'pceentradas' and creddebi.chavereferenciaqual = 'PCEEntrada'
and @is_fechada = 1 and @pode_excluir = 1 having not isnull(fu_login);
 
insert into creddebiex
select * from creddebi where creddebi.chavecodigo = @codpceentrada and creddebi.chavereferencia = 'pceentradas' and creddebi.chavereferenciaqual = 'PCEEntrada'
and @is_fechada = 1 and @pode_excluir = 1;
 
delete from creddebi where creddebi.chavecodigo = @codpceentrada and creddebi.chavereferencia = 'pceentradas' and creddebi.chavereferenciaqual = 'PCEEntrada'
and @is_fechada = 1 and @pode_excluir = 1;
 
update itenssaidas set itenssaidas.itsa_quantidader = itenssaidas.itsa_quantidade
where itenssaidas.itsa_saida = @codsaida and @is_fechada = 1 and @pode_excluir = 1;
 
update saidas set saidas.sa_status2 = 'True'
where saidas.sa_codigo = @codsaida and @is_fechada = 1 and @pode_excluir = 1;
 
insert into produtoshistoricos(codproduto,data,historico,usinclusao,dthrinclusao,valor,referenciatabela,referenciacampo,referenciacodigo,qtd,estoqueatual)
select itenssaidas.itsa_produto, curdate(), 'Entrada Materiais - Retorno Devolvel', (select cast(funcionarios.fu_codigo as char) from funcionarios where funcionarios.fu_codigo = @codfuncionario), concat(curdate(), ' ', curtime()), itenssaidas.itsa_valor, 'pceentradas', 'codpceentrada', @codpceentrada, itenssaidas.itsa_quantidader, produtos.pr_qtdestoque + itenssaidas.itsa_quantidader
from itenssaidas inner join produtos on produtos.pr_codigo = itenssaidas.itsa_produto
where itenssaidas.itsa_saida = @codsaida and @is_fechada = 1 and @pode_excluir = 1;
 
update produtos inner join itenssaidas on itenssaidas.itsa_produto = produtos.pr_codigo
set produtos.pr_qtdestoque = produtos.pr_qtdestoque + itenssaidas.itsa_quantidader
where itenssaidas.itsa_saida = @codsaida and @is_fechada = 1 and @pode_excluir = 1;
 
insert into produtoshistoricos(codproduto,data,historico,usinclusao,dthrinclusao,valor,referenciatabela,referenciacampo,referenciacodigo,qtd,estoqueatual)
select pceentradasitens.codproduto, curdate(), 'Entrada - Excluiu', (select cast(funcionarios.fu_codigo as char) from funcionarios where funcionarios.fu_codigo = @codfuncionario), concat(curdate(), ' ', curtime()), pceentradasitens.valorunitario, 'pceentrada', 'codpceentradas', @codpceentrada, pceentradasitensdetalhes.quantidade * (-1), produtos.pr_qtdestoque - pceentradasitensdetalhes.quantidade
from pceentradasitens inner join produtos on produtos.pr_codigo = pceentradasitens.codproduto inner join pceentradasitensdetalhes on pceentradasitensdetalhes.codpceentradasitens = pceentradasitens.codpceentradasitens
where pceentradasitens.codpceentradas = @codpceentrada and pceentradasitensdetalhes.quantidade <> 0 and @is_fechada = 1 and @pode_excluir = 1;
 
update produtos inner join pceentradasitens on pceentradasitens.codproduto = produtos.pr_codigo inner join pceentradasitensdetalhes on pceentradasitensdetalhes.codpceentradasitens = pceentradasitens.codpceentradasitens
set produtos.pr_qtdestoque = produtos.pr_qtdestoque - pceentradasitensdetalhes.quantidade
where produtos.pr_codigo in(select pceentradasitens.codproduto from pceentradasitens where pceentradasitens.codpceentradas = @codpceentrada)
and pceentradasitens.codpceentradas = @codpceentrada and pceentradasitensdetalhes.quantidade <> 0 and @is_fechada = 1 and @pode_excluir = 1;

delete from pceentradas                    where pceentradas.codpceentradas = @codpceentrada and @pode_excluir = 1;
delete from pceentradasitens               where pceentradasitens.codpceentradas = @codpceentrada and @pode_excluir = 1;
delete from pceentradasitensdetalhes       where pceentradasitensdetalhes.codpceentradas = @codpceentrada and @pode_excluir = 1;
delete from pceentradasitensdetalhessaidas where pceentradasitensdetalhessaidas.codpceentradas = @codpceentrada and @pode_excluir = 1;
delete from pceentradasprevisaopagamento   where pceentradasprevisaopagamento.codpceentradas = @codpceentrada and @pode_excluir = 1;
delete from pceentradasxml                 where pceentradasxml.codpceentradas = @codpceentrada and @pode_excluir = 1;

delete from notafiscal                     where notafiscal.codnotafiscal = @codnotafiscal and @pode_excluir = 1;
delete from notafiscalitensnfe             where notafiscalitensnfe.codnotafiscal = @codnotafiscal and @pode_excluir = 1;
delete from notafiscalxmls                 where notafiscalxmls.codnotafiscal = @codnotafiscal and @pode_excluir = 1;
delete from notafiscalnfe                  where notafiscalnfe.codnotafiscal = @codnotafiscal and @pode_excluir = 1;

select
if(isnull(@existeEntrada), "Entrada Não Encontrada",
    if(@is_aberta = 1 AND @pode_excluir = 1, "Sucesso: Entrada ABERTA excluída!",
        if(@is_fechada = 1 AND @pode_excluir = 1, "Sucesso: Entrada FECHADA excluída!",
            if(@temfinbaixado = 'True' and @confirmacomfinanceiro = 'False',
                if(@temsaida = 'True' and @confirmacomsaida = 'False',
                    concat('Atenção!!! Entrada com Financeiro e Saida Marcada \nPara Confirmar a Exclusão informe ''True'' na Confirmacomfinanceiro e Confirmacomsaida'),
                    concat('Atenção Tem Financeiro Baixado !!! \nPara Excluir Informe ''True'' no confirmacomfinanceiro')),
                if(@temsaida = 'True' and @confirmacomsaida = 'False',
                    concat('Atenção tem Saida de Material!!! \nPara Excluir informe ''True'' no confirmacomsaida'),
                    'Erro: Verifique se o status da entrada é válido.')
            )
        )
    )
) as Mensagem_Final;