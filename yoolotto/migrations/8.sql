ALTER TABLE `coin_transaction` ADD COLUMN `added_at` datetime;
ALTER TABLE `coin_transaction_ticket` ADD COLUMN `checked` bool;

UPDATE coin_transaction_ticket 
INNER JOIN lottery_ticket ON lottery_ticket.id = ticket_id
SET coin_transaction_ticket.checked = lottery_ticket.checked;

-- ALTER TABLE `coin_transaction_ticket` ADD COLUMN `submissions` integer NOT NULL DEFAULT 0;

-- UPDATE coin_transaction_ticket
-- LEFT OUTER JOIN lottery_ticket_play ON lottery_ticket_play.ticket_id = coin_transaction_ticket.ticket_id
-- SET submissions = (SELECT COUNT(DISTINCT submission) FROM lottery_ticket_play a1 WHERE a1.ticket_id = lottery_ticket_play.ticket_id);

CREATE TABLE `lottery_ticket_submission` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `submission` varchar(16),
    `ticket_id` integer NOT NULL,
    `added_at` datetime NOT NULL
);

ALTER TABLE `lottery_ticket_submission` ADD CONSTRAINT `ticket_id_refs_id_7512fbcc` FOREIGN KEY (`ticket_id`) REFERENCES `lottery_ticket` (`id`);

ALTER TABLE `lottery_ticket_play` ADD COLUMN `submission_id` integer AFTER `submission`;
ALTER TABLE `lottery_ticket_play` ADD CONSTRAINT `submission_id_refs_id_ab87ce90` FOREIGN KEY (`submission_id`) REFERENCES `lottery_ticket_submission` (`id`);

INSERT INTO lottery_ticket_submission(ticket_id, submission, added_at)
SELECT ticket_id, submission, MIN(added_at) AS added_at
FROM lottery_ticket_play
GROUP BY submission
ORDER BY ticket_id;

UPDATE lottery_ticket_play
SET submission_id = (SELECT id FROM lottery_ticket_submission WHERE lottery_ticket_submission.submission = lottery_ticket_play.submission);

--

CREATE TABLE `coin_transaction_submission` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `transaction_id` integer NOT NULL,
    `submission_id` integer NOT NULL UNIQUE
--    `count` integer NOT NULL
);

ALTER TABLE `coin_transaction_submission` ADD CONSTRAINT `submission_id_refs_id_603235af` FOREIGN KEY (`submission_id`) REFERENCES `lottery_ticket_submission` (`id`);
ALTER TABLE `coin_transaction_submission` ADD CONSTRAINT `transaction_id_refs_id_a27ef903` FOREIGN KEY (`transaction_id`) REFERENCES `coin_transaction` (`id`);

--

CREATE TEMPORARY TABLE _tmp_coin_transaction_delete
SELECT transaction_id FROM coin_transaction_ticket;

TRUNCATE coin_transaction_ticket;

DELETE FROM coin_transaction
WHERE id IN (SELECT transaction_id FROM _tmp_coin_transaction_delete);

UPDATE coin_wallet
SET coins = (SELECT SUM(amount) FROM coin_transaction WHERE wallet_id = coin_wallet.id);

--