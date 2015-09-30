ALTER TABLE `lottery_ticket_submission` ADD COLUMN `checked` bool NOT NULL DEFAULT 0 AFTER `ticket_id`;

UPDATE lottery_ticket_submission
LEFT OUTER JOIN lottery_ticket ON lottery_ticket.id = lottery_ticket_submission.ticket_id
SET lottery_ticket_submission.checked = lottery_ticket.checked;

-- Just Testing
ALTER TABLE `lottery_ticket` DROP `checked`;