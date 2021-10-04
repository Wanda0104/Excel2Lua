local keys = {Id = 1,tokenID = 2,tokenCount = 3,discount = 4,MaxCount = 5,map_field = 6,list_field2 = 7,}
local d = "__default_value__"
local data = { 
	[70120001] = {70120001,d,d,d,999,{["1"] = 1,["2"] = 75,},{"g","h",},},
	[70070001] = {70070001,d,d,d,10,d,{"a","b",},},
	[70130001] = {d,d,d,d,999,{["1"] = 1,["2"] = 72,},{"i","j",},},
	[32210001] = {32210001,d,1000,d,d,{["1"] = 1,["2"] = 71,},{"k","l",},},
	[52060022] = {52060022,d,900,d,d,{["1"] = 1,["2"] = 74,},{"e","f",},},
	[70110001] = {70110001,d,d,50,d,d,d,},
}
local default_value = {
	tokenCount = 100,
	tokenID = 60020001,
	map_field = {["1"] = 1,["2"] = 76,},
	discount = 0,
	list_field2 = {"c","d",},
	MaxCount = 0,
	Id = 70130001,
}
local mt = {}
mt.__index = function(t,k)
	 local key = keys[k]
	 local value = rawget(t,key)
	if value == d then return default_value[k] end
	return value
end
mt.__newindex = function(t,k)	 error( ' do not edit config ') end
mt.metatable = false
for _,v in pairs(data) do
	setmetatable(v,mt)
end
return data