
import unittest
from app import create_app, db
from app.models import Message, Room, User, AdminUser

class TestBatchDelete(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Create test data
        self.room = Room(name="Test Room", description="Test Desc", creator_id=1)
        db.session.add(self.room)
        db.session.commit()
        
        self.msgs = []
        for i in range(5):
            msg = Message(content=f"Test Msg {i}", room_id=self.room.id, user_id=None)
            db.session.add(msg)
            self.msgs.append(msg)
        db.session.commit()
        
        # Ensure admin user exists for login
        self.admin = AdminUser.query.get(1)
        if not self.admin:
            self.admin = AdminUser(username='admin', password_hash='hash')
            db.session.add(self.admin)
            db.session.commit()

    def tearDown(self):
        # Cleanup
        for msg in self.msgs:
            if msg.id: # Check if still exists in session or re-query
                m = db.session.get(Message, msg.id)
                if m: db.session.delete(m)
        if self.room.id:
            r = db.session.get(Room, self.room.id)
            if r: db.session.delete(r)
        db.session.commit()
        self.ctx.pop()

    def test_batch_delete(self):
        # Login
        with self.client.session_transaction() as sess:
            sess['admin_user_id'] = self.admin.id
            
        # Select 3 messages to delete
        ids_to_delete = [self.msgs[0].id, self.msgs[1].id, self.msgs[2].id]
        
        # Call batch delete endpoint
        response = self.client.post('/admin/messages/batch-delete', json={'ids': ids_to_delete})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'success')
        
        # Verify deletion
        remaining_count = Message.query.filter(Message.room_id == self.room.id).count()
        self.assertEqual(remaining_count, 2)
        
        deleted_msg = db.session.get(Message, ids_to_delete[0])
        self.assertIsNone(deleted_msg)
        
        kept_msg = db.session.get(Message, self.msgs[3].id)
        self.assertIsNotNone(kept_msg)

if __name__ == '__main__':
    unittest.main()
