-- deduct.lua: Atomic budget deduction
-- KEYS[1]: The Redis key for the agent's budget (e.g., "budget:dr-architect")
-- ARGV[1]: The token cost to deduct
-- ARGV[2]: A unique request ID (for future idempotency/auditing)

local balance = tonumber(redis.call('get', KEYS[1]) or 0)
local cost = tonumber(ARGV[1])

if balance >= cost then
    redis.call('decrby', KEYS[1], cost)
    -- Return the new balance so Python knows the state
    return balance - cost 
else
    -- Return -1 to signify "Insufficient Funds"
    return -1
end