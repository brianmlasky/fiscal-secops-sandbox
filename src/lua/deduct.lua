-- deduct.lua
local balance = tonumber(redis.call('get', KEYS[1]) or 0)
local cost = tonumber(ARGV[1])
local request_id = ARGV[2]

-- 1. Idempotency Check
local idempotency_key = "idempotency:" .. KEYS[1] .. ":" .. request_id
local previous_result = redis.call('get', idempotency_key)

if previous_result then
    local cached = cjson.decode(previous_result)
    return {cached.new_balance, cached.prev_balance, cached.was_success}
end

-- 2. Deduct Logic
local was_success = false
local new_balance = balance

if balance >= cost then
    redis.call('decrby', KEYS[1], cost)
    new_balance = balance - cost
    was_success = true
end

-- 3. Cache result and return
local result = {new_balance, balance, was_success}
redis.call('setex', idempotency_key, 86400, cjson.encode(result))

return result