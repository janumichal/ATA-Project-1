#!/usr/bin/env python3
"""
Example of usage/test of Cart controller implementation.
Extended by custom tests by CEG and combine
"""

from platform import java_ver
from cartctl import CartCtl, Status as Status_ctl
from cart import Cart, CargoReq, Status as Status_cart
from jarvisenv import Jarvis
import factory
import unittest

def log(msg):
    "simple logging"
    print("%s" %msg)

def log_on_move(c: Cart):
    log('%d: Cart is moving %s->%s' % (Jarvis.time(), c.pos, c.data))
    log(c)

def log_add_load(cargo_req: CargoReq):
    log("%d: Requesting %s at %s" %(Jarvis.time(), cargo_req, cargo_req.src))

def log_on_load(c: Cart, cargo_req: CargoReq):
    log('%d: Cart at %s: loading: %s' % (Jarvis.time(), c.pos, cargo_req))
    log(c)

def log_on_unload(c: Cart, cargo_req: CargoReq):
    log('%d: Cart at %s: unloading: %s' % (Jarvis.time(), c.pos, cargo_req))
    log(c)

def req_status_check(test ,ctl: CartCtl, stat: Status_ctl):
    "Scheduler task to check status of request"
    test.assertEqual(ctl.status, stat)

class TestCartRequests(unittest.TestCase):

    def setUp(self):
        "define setup before test"
        Jarvis.TRACKS = factory.Tracks([
        factory.Track('A', 'B', 20),
        factory.Track('B', 'A', 30),
        factory.Track('B', 'C', 20),
        factory.Track('C', 'D', 20),
        factory.Track('D', 'A', 10),
        ])
        Jarvis.reset_scheduler()
        print("")

    def test_happy(self):
        "Happy-path test"

        def add_load(c: CartCtl, cargo_req: CargoReq):
            "callback for schedulled load"
            log('%d: Requesting %s at %s' % \
                (Jarvis.time(), cargo_req, cargo_req.src))
            c.request(cargo_req)

        def on_move(c: Cart):
            "example callback (for assert)"
            # put some asserts here
            log('%d: Cart is moving %s->%s' % (Jarvis.time(), c.pos, c.data))

        def on_load(c: Cart, cargo_req: CargoReq):
            "example callback for logging"
            log('%d: Cart at %s: loading: %s' % (Jarvis.time(), c.pos, cargo_req))
            log(c)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            "example callback (for assert)"
            # put some asserts here
            log('%d: Cart at %s: unloading: %s' % (Jarvis.time(), c.pos, cargo_req))
            log(c)
            self.assertEqual('loaded', cargo_req.context)
            cargo_req.context = 'unloaded'
            if cargo_req.content == 'helmet':
                self.assertEqual('B', c.pos)
            if cargo_req.content == 'heart':
                self.assertEqual('A', c.pos)
            #if cargo_req.content.startswith('bracelet'):
            #    self.assertEqual('C', c.pos)
            if cargo_req.content == 'braceletR':
                self.assertEqual('A', c.pos)
            if cargo_req.content == 'braceletL':
                self.assertEqual('C', c.pos)

        # Setup Cart
        # 4 slots, 150 kg max payload capacity, 2=max debug
        cart_dev = Cart(4, 150, 0)
        cart_dev.onmove = on_move

        # Setup Cart Controller
        c = CartCtl(cart_dev, Jarvis)

        # Setup Cargo to move
        helmet = CargoReq('A', 'B', 20, 'helmet')
        helmet.onload = on_load
        helmet.onunload = on_unload

        heart = CargoReq('C', 'A', 40, 'heart')
        heart.onload = on_load
        heart.onunload = on_unload

        braceletR = CargoReq('D', 'A', 40, 'braceletR')
        braceletR.onload = on_load
        braceletR.onunload = on_unload

        braceletL = CargoReq('D', 'C', 40, 'braceletL')
        braceletL.onload = on_load
        braceletL.onunload = on_unload

        # Setup Plan
        Jarvis.reset_scheduler()
        #         when  event     called_with_params
        Jarvis.plan(10, add_load, (c,helmet))
        Jarvis.plan(45, add_load, (c,heart))
        Jarvis.plan(40, add_load, (c,braceletR))
        Jarvis.plan(25, add_load, (c,braceletL))
        
        # Exercise + Verify indirect output
        #   SUT is the Cart.
        #   Exercise means calling Cart.request in different time periods.
        #   Requests are called by add_load (via plan and its scheduler).
        #   Here, we run the plan.
        Jarvis.run()

        # Verify direct output
        log(cart_dev)
        self.assertTrue(cart_dev.empty())
        self.assertEqual('unloaded', helmet.context)
        self.assertEqual('unloaded', heart.context)
        self.assertEqual('unloaded', braceletR.context)
        self.assertEqual('unloaded', braceletL.context)
        #self.assertEqual(cart_dev.pos, 'C')

    def test_ceg_01(self):
        "Test [1] of CEG table: No requests"

        def on_move(c: Cart):
            log_on_move(c)
            self.fail("Cart Sould not be moving (no requests)")

        cart = Cart(1, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        Jarvis.run()
        
        self.assertEqual(cart.pos, 'A')
        self.assertEqual(Status_cart.Idle, cart.status)
        self.assertEqual(None, cart.data)
        self.assertTrue(cart.empty())
        self.assertEqual(cart.load_sum(), 0)
        self.assertFalse(cart.any_prio_cargo())
        if(not cart.any_prio_cargo()):
            self.fail("Can't call atribute 'prio' on None in function: Cart.get_prio_idx()")
        else:
            self.assertEqual(cart.get_prio_idx(), -1)
        self.assertNotEqual(cart.get_free_slot(), -1)
        
    def test_ceg_02(self):
        "Test [2] of CEG table: One non-priority request loaded"

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            if(c.empty()):
                self.assertEqual(c.pos, 'A')
                self.assertEqual(c.data, 'B')
            else:
                self.assertEqual(c.pos, 'B')
                self.assertEqual(c.data, 'C')
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertFalse(c.any_prio_cargo())
            self.assertEqual(c.pos, 'B')
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            self.assertEqual(cargo_req.content, "item_01")
            self.assertFalse(cargo_req.prio)
            self.assertEqual(cargo_req.src, "B")
            self.assertEqual(cargo_req.dst, "C")
            self.assertEqual(cargo_req.weight, 10)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(cargo_req.content, "item_01")
            self.assertEqual(c.pos, 'C')
            cargo_req.context = "unloaded"

        cart = Cart(1, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('B', 'C', 10, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(35, req_status_check, (self, cart_ctl,Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)

    def test_ceg_03(self):
        "Test [3] of CEG table: One priority request loaded"

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            if(c.empty()):
                self.assertEqual(c.pos, 'A')
                self.assertEqual(c.data, 'B')
            else:
                self.assertEqual(c.pos, 'B')
                self.assertEqual(c.data, 'C')
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertTrue(c.any_prio_cargo())
            self.assertEqual(c.pos, 'B')
            self.assertLess(Jarvis.time(), cargo_req.born + 120)
            self.assertGreater(Jarvis.time(), cargo_req.born + 60)
            self.assertEqual(cargo_req.content, "item_01")
            self.assertTrue(cargo_req.prio)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(cargo_req.content, "item_01")
            self.assertEqual(c.pos, 'C')
            cargo_req.context = "unloaded"

        Jarvis.TRACKS = factory.Tracks([
        factory.Track('A', 'B', 90),
        factory.Track('B', 'A', 30),
        factory.Track('B', 'C', 20),
        factory.Track('C', 'D', 20),
        factory.Track('D', 'A', 10),
        ])


        cart = Cart(1, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('B', 'C', 10, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(110, req_status_check, (self, cart_ctl, Status_ctl.UnloadOnly))
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)

    def test_ceg_04(self):
        "Test [4] of CEG table: Cart didn't arrive in time"

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.pos, 'A')
            self.assertEqual(c.data, 'B')

        def on_load(c: Cart, cargo_req: CargoReq):
            self.fail("Cart shouldn't make it in time")


        Jarvis.TRACKS = factory.Tracks([
        factory.Track('A', 'B', 160),
        factory.Track('B', 'A', 30),
        factory.Track('B', 'C', 20),
        factory.Track('C', 'D', 20),
        factory.Track('D', 'A', 10),
        ])


        cart = Cart(1, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('B', 'C', 10, "item_01")
        item_01.onload = on_load

        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(110, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, None)

    def test_ceg_05(self):
        "Test [5] of CEG table: non-priority request but no space on cart"

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.fail("The cart shouldn't move because there is no space for cargo.")

        cart = Cart(1, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('B', 'C', 60, "item_01")

        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(35, req_status_check, (self, cart_ctl, Status_ctl.Idle))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, None)
        self.assertEqual(cart.pos, 'A')
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)

    def test_ceg_06(self):
        "Test [6] of CEG table: non-priority request with empty slots but loaded over limit."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            if(Jarvis.time() < 15):
                self.assertFalse(c.any_prio_cargo())
                self.assertEqual(cargo_req.content, "item_01")
                self.assertLess(Jarvis.time(), cargo_req.born + 60)
            else:
                self.assertTrue(c.any_prio_cargo())
                self.assertEqual(cargo_req.content, "item_02")
                self.assertLess(Jarvis.time(), cargo_req.born + 120)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            if(Jarvis.time() < 80):
                self.assertEqual(cargo_req.content, "item_01")
            else:
                self.assertEqual(cargo_req.content, "item_02")
            self.assertEqual(c.pos, 'D')
            cargo_req.context = "unloaded"

        cart = Cart(2, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('A', 'D', 50, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('C', 'D', 10, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(11, add_load, (cart_ctl,item_02))
        Jarvis.plan(50, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        Jarvis.plan(130, req_status_check, (self, cart_ctl, Status_ctl.UnloadOnly))
        

        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)

    def test_ceg_07(self):
        "Test [7] of CEG table: non-priority request with full slots but not loaded to it's limit."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            if(Jarvis.time() < 15):
                self.assertFalse(c.any_prio_cargo())
                self.assertEqual(cargo_req.content, "item_01")
                self.assertLess(Jarvis.time(), cargo_req.born + 60)
            else:
                self.assertTrue(c.any_prio_cargo())
                self.assertEqual(cargo_req.content, "item_02")
                self.assertLess(Jarvis.time(), cargo_req.born + 120)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            if(Jarvis.time() < 80):
                self.assertEqual(cargo_req.content, "item_01")
            else:
                self.assertEqual(cargo_req.content, "item_02")
            self.assertEqual(c.pos, 'D')
            cargo_req.context = "unloaded"

        cart = Cart(1, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('A', 'D', 10, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('C', 'D', 10, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(11, add_load, (cart_ctl,item_02))
        Jarvis.plan(50, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        Jarvis.plan(130, req_status_check, (self, cart_ctl, Status_ctl.UnloadOnly))
        

        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        

    def test_combine_01(self):
        "Test 1 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'A')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'B')
            cargo_req.context = "unloaded"

        cart = Cart(1, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('A', 'B', 15, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('A', 'B', 15, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(35, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)

    def test_combine_02(self):
        "Test 2 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'A')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            self.assertEqual(cargo_req.content, "item_01")
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'C')
            cargo_req.context = "unloaded"

        cart = Cart(2, 150, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('A', 'C', 80, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(35, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_03(self):
        "Test 3 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'A')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'D')
            cargo_req.context = "unloaded"

        cart = Cart(3, 150, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('A', 'D', 15, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('A', 'D', 15, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(35, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)

    def test_combine_04(self):
        "Test 4 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'B')
            if(Jarvis.time() < cargo_req.born + 60):
                self.assertFalse(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 60)
            else:
                self.assertTrue(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 120)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'A')
            cargo_req.context = "unloaded"

        cart = Cart(1, 500, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('B', 'A', 40, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('B', 'A', 40, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(35, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        Jarvis.plan(90, req_status_check, (self, cart_ctl, Status_ctl.UnloadOnly))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)

    def test_combine_05(self):
        "Test 5 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'B')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            self.assertEqual(cargo_req.content, "item_01")
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'C')
            cargo_req.context = "unloaded"

        cart = Cart(3, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('B', 'C', 30, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(35, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_06(self):
        "Test 6 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'B')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            self.assertEqual(cargo_req.content, "item_01")
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'D')
            cargo_req.context = "unloaded"

        cart = Cart(2, 500, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('B', 'D', 400, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(35, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_07(self):
        "Test 7 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'C')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'A')
            cargo_req.context = "unloaded"

        cart = Cart(2, 150, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('C', 'A', 15, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload
        item_02 = CargoReq('C', 'A', 15, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(11, add_load, (cart_ctl,item_02))
        Jarvis.plan(55, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_08(self):
        "Test 8 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'C')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            self.assertEqual(cargo_req.content, "item_01")
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'B')
            cargo_req.context = "unloaded"

        cart = Cart(3, 150, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('C', 'B', 80, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(35, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_09(self):
        "Test 9 of combine table."


        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'C')
            if(Jarvis.time() < cargo_req.born + 60):
                self.assertFalse(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 60)
            else:
                self.assertTrue(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 120)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'D')
            cargo_req.context = "unloaded"

        cart = Cart(1, 500, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('C', 'D', 200, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('C', 'D', 200, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(35, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        Jarvis.plan(130, req_status_check, (self, cart_ctl, Status_ctl.UnloadOnly))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)

    def test_combine_10(self):
        "Test 10 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'D')
            self.assertTrue(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 120)
            self.assertEqual(cargo_req.content, "item_01")
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'A')
            cargo_req.context = "unloaded"

        cart = Cart(3, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('D', 'A', 30, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(80, req_status_check, (self, cart_ctl, Status_ctl.UnloadOnly))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_11(self):
        "Test 11 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'D')
            if(Jarvis.time() < cargo_req.born + 60):
                self.assertFalse(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 60)
            else:
                self.assertTrue(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 120)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'B')
            cargo_req.context = "unloaded"

        cart = Cart(2, 500, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('D', 'B', 200, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('D', 'B', 200, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(70, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        Jarvis.plan(80, req_status_check, (self, cart_ctl, Status_ctl.UnloadOnly))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_12(self):
        "Test 12 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'D')
            if(cargo_req.content == "item_02"):
                self.assertFalse(c.any_prio_cargo())
            else:
                self.assertTrue(c.any_prio_cargo())
                
            self.assertLess(Jarvis.time(), cargo_req.born + 120)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'C')
            cargo_req.context = "unloaded"

        cart = Cart(1, 150, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('D', 'C', 40, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('D', 'C', 40, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(80, req_status_check, (self, cart_ctl, Status_ctl.UnloadOnly))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, None)
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)

    def test_combine_13(self):
        "Test 13 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'B')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'C')
            cargo_req.context = "unloaded"

        cart = Cart(4, 150, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('B', 'C', 15, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('B', 'C', 15, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(50, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_14(self):
        "Test 14 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'A')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            self.assertEqual(cargo_req.content, "item_01")
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'D')
            cargo_req.context = "unloaded"

        cart = Cart(4, 150, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('A', 'D', 80, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(35, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_15(self):
        "Test 15 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'B')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'A')
            cargo_req.context = "unloaded"

        cart = Cart(4, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('B', 'A', 15, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('B', 'A', 15, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(50, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)

    def test_combine_16(self):
        "Test 16 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'A')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'B')
            cargo_req.context = "unloaded"

        cart = Cart(4, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('A', 'B', 15, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('A', 'B', 15, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(50, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)

    def test_combine_18(self):
        "Test 18 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'D')
            if(Jarvis.time() < cargo_req.born + 60):
                self.assertFalse(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 60)
            else:
                self.assertTrue(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 120)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'A')
            cargo_req.context = "unloaded"

        cart = Cart(4, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('D', 'A', 15, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('D', 'A', 15, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(75, req_status_check, (self, cart_ctl, Status_ctl.UnloadOnly))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_19(self):
        "Test 19 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'C')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'A')
            cargo_req.context = "unloaded"

        cart = Cart(4, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('C', 'A', 15, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('C', 'A', 15, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(65, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_20(self):
        "Test 20 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'B')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            self.assertEqual(cargo_req.content, "item_01")
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'A')
            cargo_req.context = "unloaded"

        cart = Cart(1, 500, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('B', 'A', 400, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(35, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_21(self):
        "Test 21 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'A')
            if(Jarvis.time() < cargo_req.born + 60):
                self.assertFalse(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 60)
            else:
                self.assertTrue(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 120)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'C')
            cargo_req.context = "unloaded"

        cart = Cart(1, 500, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('A', 'C', 200, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('A', 'C', 200, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(90, req_status_check, (self, cart_ctl, Status_ctl.UnloadOnly))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_22(self):
        "Test 22 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'A')
            self.assertFalse(c.any_prio_cargo())
            self.assertLess(Jarvis.time(), cargo_req.born + 60)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'B')
            cargo_req.context = "unloaded"

        cart = Cart(1, 500, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('A', 'B', 200, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('A', 'B', 200, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(45, req_status_check, (self, cart_ctl, Status_ctl.Normal))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)
        
    def test_combine_24(self):
        "Test 24 of combine table."

        def add_load(c: CartCtl, cargo_req: CargoReq):
            log_add_load(cargo_req)
            c.request(cargo_req)

        def on_move(c: Cart):
            log_on_move(c)
            self.assertEqual(c.status, Status_cart.Moving)

        def on_load(c: Cart, cargo_req: CargoReq):
            log_on_load(c, cargo_req)
            self.assertFalse(c.empty())
            self.assertEqual(c.pos, 'A')
            if(Jarvis.time() < cargo_req.born + 60):
                self.assertFalse(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 60)
            else:
                self.assertTrue(c.any_prio_cargo())
                self.assertLess(Jarvis.time(), cargo_req.born + 120)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log_on_unload(c, cargo_req)
            self.assertEqual(c.pos, 'D')
            cargo_req.context = "unloaded"

        cart = Cart(1, 50, 0)
        cart.onmove = on_move

        cart_ctl = CartCtl(cart, Jarvis)

        item_01 = CargoReq('A', 'D', 15, "item_01")
        item_01.onload = on_load
        item_01.onunload = on_unload

        item_02 = CargoReq('A', 'D', 15, "item_02")
        item_02.onload = on_load
        item_02.onunload = on_unload


        Jarvis.plan(10, add_load, (cart_ctl,item_01))
        Jarvis.plan(15, add_load, (cart_ctl,item_02))
        Jarvis.plan(90, req_status_check, (self, cart_ctl, Status_ctl.UnloadOnly))
        
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual(item_01.context, "unloaded")
        self.assertEqual(item_02.context, "unloaded")
        self.assertEqual(cart_ctl.status, Status_ctl.Idle)


if __name__ == "__main__":
    unittest.main()
