// ==UserScript==
// @name         Raiffeisen RS data export
// @version      1.0
// @description  Raiffeisen RS data export
// @author       Evgenii Novikov
// @match        https://rol.raiffeisenbank.rs/Retail/*
// @grant        none
// ==/UserScript==

(async function () {
    'use strict';

    async function getTx() {
        // Берем транзакции за 2023 год
        const filter = '"filterParam":{"FromDate":"01.01.2023","ToDate":"01.01.2024"}'

        // URL фронтового API Райфа
        const base = "https://rol.raiffeisenbank.rs/Retail/Protected/Services/DataService.svc/"
        // Получаем банковские счета
        const accounts = await fetch(base + "GetAllAccountBalance",
            {
                body: '{"gridName":"RetailAccountBalancePreviewFlat-L"}',
                method: "POST"
            }).then(res => res.json());

        // Получаем транзакции
        const transactions = {};
        for (let number of new Set(accounts.map(a => a[1]))) {
            // Скачиваем информацию о транзакции
            transactions[number] = await fetch(base + "GetTransactionalAccountTurnover", {
                body: '{"gridName":"RetailAccountTurnoverTransactionPreviewMasterDetail-S",' +
                    '"productCoreID":"541","accountNumber":"' + number + '",' + filter + '}',
                method: "POST"
            }).then(res => res.json());
        }

        return transactions;
    }

    if (location.hash === "#download") {
        alert("Скачивание транзакций за 2023 год скоро начнется, подождите");

        // Сохраняем транзакции как файл
        const element = document.createElement('a');
        // Кодируем данные
        element.href = URL.createObjectURL(new Blob([JSON.stringify({ transactions: await getTx() })],
            { type: "application/json" }));
        // Сохраняем в загрузки
        element.download = 'Raiff_2023_' + new Date().toISOString() + '.json';
        element.click();
    }

    if (location.hash === "#send") {
        alert("Отправка транзакций за 2023 год скоро начнется, подождите");
        const value = JSON.stringify({ transactions: await getTx() });

        addEventListener('click', () => {
            // Открываем RtxData
            const rtxdata = window.open("https://rtxdata.github.io")
            // Отправляем данные
            rtxdata.postMessage({
                name: 'Raiff_2023_' + new Date().toISOString() + '.json', value
                // Данные может прочитать только RtxData
            }, "https://rtxdata.github.io");
        });

        alert("Нажмите в любую точку");
    }
})();

