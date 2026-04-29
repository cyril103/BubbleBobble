def bubble_hits_enemy(bubble, enemy) -> bool:
    return bubble.can_capture_enemy() and bubble.rect.colliderect(enemy.rect)


def player_hits_enemy(player, enemy) -> bool:
    return player.rect.colliderect(enemy.rect)


def player_stomps_trapped_enemy(player, enemy) -> bool:
    return enemy.trapped and player.rect.colliderect(enemy.rect)
