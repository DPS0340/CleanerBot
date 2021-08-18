import * as hostile from "./hostile.js";

const ip = "13.125.8.153";
// const ip = "127.0.0.1";

hostile.set(ip, "cleanerbot.dcinside.com");
// hostile.set(ip, "_acme-challenge.cleanerbot.dcinside.com");
console.log("cleanerbot.dcinside.com -> 봇 서버 IP DNS 등록 추가!");

prompt("Enter를 눌러서 종료해 주세요!");
